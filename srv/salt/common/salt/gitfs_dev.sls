#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install gitfs file server and development formulas
##

salt-gitfs:
  pkg.installed:
    - names:
      - python-dulwich
    - require_in:
      - service: salt-master
      - service: salt-minion

# gitfs configuration file
$with /etc/salt/master.d/gitfs.conf.dev:
  file:
    - absent
    - require_in:
      - file: /srv/salt/top.sls

  /etc/salt/master.d/gitfs.conf:
    file.managed:
      - source: salt://salt/files/master.d/gitfs.conf.dev
      - user: root
      - group: root
      - mode: 640

# use master gitfs configuration file
$with /etc/salt/minion.d/gitfs.conf.dev:
  file:
    - absent
    - require_in:
      - file: /srv/salt/top.sls

  /etc/salt/minion.d/gitfs.conf:
    file.managed:
      - source: salt://salt/files/master.d/gitfs.conf.dev
      - user: root
      - group: root
      - mode: 640

