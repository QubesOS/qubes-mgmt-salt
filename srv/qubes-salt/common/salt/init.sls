#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Install salt base
##

# TODO:
#   - Need to restart salt servers after updating?

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

$with salt-dependencies:
  pkg.installed:
    - names:
      - git
      - python
      - $SaltMap.python_dev
      - $SaltMap.python_m2crypto
      - $SaltMap.python_openssl

  $if installed_by_repo:
    salt:
      pkg.installed:
        - name: $SaltMap.salt

  # binddirs script to bind /srv & /etc/salt to /rw/usrlocal/srv...
  $if __grains__['virtual_subtype'] == 'Xen PV DomU':
    /usr/lib/salt/bind-directories:
      file.managed:
        - source: salt://salt/files/bind-directories
        - makedirs: True
        - user: root
        - group: root
        - mode: 755

  # Base state top file
  /srv/qubes-salt/top.sls:
    file.managed:
      - source: salt://salt/files/top.sls
      - replace: False
      - makedirs: True
      - user: root
      - group: root
      - mode: 640

  # Salt file and directory permissions
  /srv/qubes-salt:
    file.directory:
      - user: root
      - group: root
      - dir_mode: 750
      - file_mode: 640
      - recurse:
        - user
        - group
        - mode

  # salt-servers file and directory permissions
  /srv/salt-servers:
    file.directory:
      - user: root
      - group: root
      - dir_mode: 750
      - file_mode: 640
      - recurse:
        - user
        - group
        - mode

  # Qubes pillar file and directory permissions
  /srv/qubes-pillar:
    file.directory:
      - user: root
      - group: root
      - dir_mode: 750
      - file_mode: 640
      - recurse:
        - user
        - group
        - mode

