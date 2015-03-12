#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install salt-syndic and its configuration files
##

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

salt-syndic:
  $if installed_by_repo:
    pkg.installed:
      - name: $SaltMap.salt
  $else:
    pip.installed:
      - name: salt
  service.running:
    - name: salt-syndic
    - enable: True
    - watch:
      - file: /etc/systemd/system/salt-syndic.service

# salt-syndic unit file
/etc/systemd/system/salt-syndic.service:
  file.managed:
    - source: salt://salt/files/salt-syndic.service
    - user: root
    - group: root
    - mode: 755
