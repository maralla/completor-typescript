# -*- coding: utf-8 -*-

import json
import logging
import re
from completor import Completor, vim
from completor.compat import to_unicode


logger = logging.getLogger('completor')

PREFIX = re.compile('(\w+)$')


class Typescript(Completor):
    filetype = 'typescript'
    aliases = ['typescript.tsx', 'typescript.jsx']

    def __init__(self):
        Completor.__init__(self)
        self._action = None
        self.open_files = set()
        self._seq = 0

    @property
    def seq(self):
        self._seq += 1
        return self._seq

    def is_message_end(self, msg):
        return b'"command":"completions"' in msg or \
            b'"command":"definition"' in msg or \
            b'"command":"quickinfo"' in msg

    def get_cmd_info(self, action):
        binary = self.get_option('tsserver_binary') or 'tsserver'
        return vim.Dictionary(
            cmd=[binary],
            ftype=self.filetype,
            is_daemon=True,
            is_sync=False)

    def _format_request(self, cmd, **kwargs):
        return {
            'seq': self.seq,
            'type': 'request',
            'command': cmd,
            'arguments': kwargs
        }

    def _prepare_cmd(self, fname, cmd):
        if fname not in self.open_files:
            open_cmd = self._format_request('open', file=fname)
            cmds = [open_cmd, cmd]
            self.open_files.add(fname)
        else:
            reload_cmd = self._format_request(
                'reload', tmpfile=self.tempname, file=fname)
            cmds = [reload_cmd, cmd]
        return '\n'.join([json.dumps(c) for c in cmds])

    def prepare_complete(self, fname, line, col):
        match = PREFIX.search(self.input_data)
        prefix = match.group() if match else ''
        logger.info('%s, %s, %s', line, col, prefix)
        completion_cmd = self._format_request(
            'completions',
            file=fname,
            line=line,
            offset=col + 1,
            prefix=prefix
        )
        return self._prepare_cmd(fname, completion_cmd)

    def prepare_definition(self, fname, line, col):
        def_cmd = self._format_request('definition', file=fname, line=line,
                                       offset=col + 1)
        return self._prepare_cmd(fname, def_cmd)

    def prepare_doc(self, fname, line, col):
        doc_cmd = self._format_request('quickinfo', file=fname, line=line,
                                       offset=col + 1)
        return self._prepare_cmd(fname, doc_cmd)

    def prepare_request(self, action):
        self._action = action
        fname = self.filename
        line, col = self.cursor
        logger.info(action)
        if action == b'complete':
            return self.prepare_complete(fname, line, col)
        if action == b'definition':
            return self.prepare_definition(fname, line, col)
        if action == b'doc':
            return self.prepare_doc(fname, line, col)
        return ''

    def on_complete(self, data):
        try:
            res = json.loads(to_unicode(data[-1], 'utf-8'))
        except Exception as e:
            logger.exception(e)
            res = {}
        ret = []
        match = PREFIX.search(self.input_data)
        for item in res.get('body', []):
            if not self.input_data.rstrip().endswith('.') and \
                    (not match or
                     match.group().lower() not in item['name'].lower()):
                continue
            ret.append({'word': item['name'], 'menu': item['kind']})
        return ret

    @staticmethod
    def get_cursor_word():
        try:
            return vim.Function('expand')('<cword>')
        except vim.error:
            return

    def on_definition(self, data):
        try:
            res = json.loads(to_unicode(data[-1], 'utf-8'))
        except Exception as e:
            logger.exception(e)
            res = {}
        word = self.get_cursor_word()
        if not word:
            return []

        ret = []
        for item in res.get('body', []):
            ret.append({
                'filename': item['file'],
                'lnum': item['start']['line'],
                'col': item['start']['offset'],
                'name': word
            })
        return ret

    def on_doc(self, data):
        try:
            res = json.loads(to_unicode(data[-1], 'utf-8'))
        except Exception as e:
            logger.exception(e)
            res = {}
        body = res.get('body')
        if not body:
            return []

        display = body['displayString']
        doc = body['documentation']
        nl = ('\n\n' if display else '') if doc else ''
        return [display + nl + doc]
