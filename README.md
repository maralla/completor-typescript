completor-typescript
====================

Typescript autocompletion for [completor.vim](https://github.com/maralla/completor.vim).

![Demo](https://i.imgur.com/2Zsee68.gif)

Install
-------

[Install completor.vim](https://github.com/maralla/completor.vim#install) first.

* [pack](https://github.com/maralla/pack)

```bash
$ pack install maralla/completor-typescript
```

* [vim-plug](https://github.com/junegunn/vim-plug)

```vim
Plug 'maralla/completor-typescript'
```

Tips
----

Change `tsserver` location:
```vim
let g:completor_tsserver_binary = '/path/to/tsserver'
```

Goto definition:
```vim
:call completor#do('definition')
```

View documentation:
```vim
:call completor#do('doc')
```
