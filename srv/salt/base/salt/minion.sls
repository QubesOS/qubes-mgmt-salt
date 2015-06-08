#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install / enable salt-minion
##

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

salt-minion:
  $if installed_by_repo:
    pkg.installed: []
  $else:
    pip.installed:
      - name: salt
  service.running:
    - name: salt-minion
    - enable: True
    - watch:
      - file: /etc/salt/minion
      - file: /etc/systemd/system/salt-minion.service

# salt-minion unit file
/etc/systemd/system/salt-minion.service:
  file.managed:
    - source: salt://salt/files/salt-minion.service
    - user: root
    - group: root
    - mode: 755
