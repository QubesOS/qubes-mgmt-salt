# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install salt configuration files
##

# salt-minion master configuration file
/etc/salt/minion:
  file.managed:
    - source: salt://salt/files/minion
    - user: root
    - group: root
    - mode: 644
    - onlyif: which salt-minion

# salt-minion drop-in configuration files
/etc/salt/minion.d:
  file.recurse:
    - source: salt://salt/files/minion.d
    - makedirs: True
    - clean: False
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - onlyif: which salt-minion

# salt-master configuration file
/etc/salt/master:
  file.managed:
    - source: salt://salt/files/master
    - user: root
    - group: root
    - mode: 640
    - onlyif: which salt-master

# salt-master drop-in configuration files
/etc/salt/master.d:
  file.recurse:
    - source: salt://salt/files/master.d
    - makedirs: True
    - clean: False
    - user: root
    - group: root
    - dir_mode: 755
    - file_mode: 644
    - onlyif: which salt-master

