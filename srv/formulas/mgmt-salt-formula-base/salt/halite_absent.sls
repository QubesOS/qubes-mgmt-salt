#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Disable salt-halite
##

# halite configuration file
/etc/salt/master.d/halite.conf:
  file:
    - absent

