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

  #$else:
  #  $with salt-pip-dependencies:
  #    # python-jinja2    # APT: 2.7.2-2
  #    pip.installed:
  #      - names:
  #        - pyzmq             # PIP: 14.0.1
  #        - PyYAML            # PIP: 0.8.4
  #        - pycrypto          # PIP: 2.6.1
  #        - msgpack-python    # PIP: 0.3.0
  #        - jinja2            # 2.7.2
  #        - psutil            # not-installed
  #        - wheel
  #      - require:
  #        - pkg: pip-dependencies

  #    salt:
  #      # Install from git
  #      pip.installed:
  #        - name: git+https://github.com/saltstack/salt.git@v2014.7.0#egg=salt
  #        - no_deps: True # We satisfy deps already since we cant build m2crypto on debian/ubuntu
  #        - install_options: --force-installation-into-system-dir
  #        - install_options: --prefix=/usr
  #        - use_wheel: True
  #        - upgrade: False

  # XXX: not needed for dom0
  # binddirs script
  /usr/lib/salt/bind-directories:
    file.managed:
      - source: salt://salt/files/bind-directories
      - makedirs: True
      - user: root
      - group: root
      - mode: 755

  # Extended top file
  /srv/salt/top.sls:
    file.managed:
      - source: salt://salt/files/top.sls
      - replace: False
      - makedirs: True
      - user: root
      - group: root
      - mode: 640

  # salt file and directory permissions
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

  # salt-formulas file and directory permissions
  /srv/salt-formulas:
    file.directory:
      - user: root
      - group: root
      - dir_mode: 750
      - file_mode: 640
      - recurse:
        - user
        - group
        - mode

  # pillar file and directory permissions
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
