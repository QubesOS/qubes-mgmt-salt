#!/bin/bash

# Pathogen
# https://github.com/tpope/vim-pathogen
mkdir -p ~/.vim/autoload ~/.vim/bundle && \
curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim

# Install sensible plugin
cd ~/.vim/bundle && \
	git clone git://github.com/tpope/vim-sensible.git

# Surround plugin
# Says to installpathogen.vim first
# https://github.com/tpope/vim-surround
cd ~/.vim/bundle
git clone git://github.com/tpope/vim-surround.git
