#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install / enable salt-master
#
# TODO:
#   - generate keys automatically (ONLY ON NEW INSTALLS)
#   - auto accept minions keys somehow
#   - maybe keys should be pillars so all minions won't see them
##

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

salt-master:
  $if installed_by_repo:
    pkg.installed:
      - names:
        - $SaltMap.salt
        - $SaltMap.salt_master
  $else:
    pip.installed:
      - name: salt
  service.running:
    - name: salt-master
    - enable: True
    - watch:
      - file: /etc/salt/master
      - file: /etc/systemd/system/salt-master.service

# salt-master unit file
/etc/systemd/system/salt-master.service:
  file.managed:
    - source: salt://salt/files/salt-master.service
    - user: root
    - group: root
    - mode: 755

