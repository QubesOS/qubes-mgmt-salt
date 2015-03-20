# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install user salt and pillar directories for personal state configurations 
#
# Includes a simple locale state file
#
# NOTE: 
#   User defined scripts will not be removed on removal of qubes-salt-config
#   by design nor will they be modified on any updates, other than permissions
#   being enforced.
##

# User state file and directory permissions
/srv/salt:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 750
    - file_mode: 640
    - recurse:
      - user
      - group
      - mode

# User state top file
/srv/salt/top.sls:
  file.managed:
    - source: salt://salt-user/files/top.sls
    - replace: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 640
    - require:
      - file: /srv/salt

# User pillar file and directory permissions
/srv/pillar:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 750
    - file_mode: 640
    - recurse:
      - user
      - group
      - mode

# User pillar top file
/srv/pillar/top.sls:
  file.managed:
    - source: salt://salt-user/files/pillar.sls
    - replace: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 640
    - require:
      - file: /srv/pillar

# Sample locale state directory
/srv/salt/locale:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 750
    - file_mode: 640
    - recurse:
      - user
      - group
      - mode

# Sample locale state file
/srv/salt/locale/init.sls:
  file.managed:
    - source: salt://salt-user/files/locale.sls
    - replace: False
    - makedirs: True
    - user: root
    - group: root
    - mode: 640
    - require:
      - file: /srv/salt/locale

