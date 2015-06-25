===============
Privacy Formula
===============

This formula will install some privacy related configuration as well as change the .bash* configuration files for
the root and /home/user`

Files updates for /root and /home/user:

   .bash_aliases
   .bash_git
   .bash_history
   .bash_logout
   .bash_profile
   .bashrc
   .vim
   .vimrc

.bash_history is cleared and prevented from being used
.vimrc is configurated not to store vim history 

.. note::

Currently some random package are also installed: telenet and apt-file for Debian which will be removed from formula

Available states
================

.. contents::
    :local:

``privacy``
------------

