# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Other Salt States
# ==================
#
# os:
#   Installs telnet and apt-file (in Debian) as well as enhanced .bash* and .vimrc
#   configuration files.  The .bash* files prevent .bash_history from being written
#   to and .vimrc prevent vim history from being written
# --> qubesctl state.sls os

vm_other:
  'vm_other:true':
    - match: pillar
    - os
