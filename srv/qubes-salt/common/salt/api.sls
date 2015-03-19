#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install salt-api
##

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

salt-api:
  service.enabled:
    - name: salt-api
      $if installed_by_repo:
        - require:
          - pkg: $SaltMap.salt_master
      $else:
        - require:
          - pip: salt-master

# salt-api unit file
/etc/systemd/system/salt-api.service:
  file.managed:
    - source: salt://salt/files/salt-api.service
    - user: root
    - group: root
    - mode: 755
