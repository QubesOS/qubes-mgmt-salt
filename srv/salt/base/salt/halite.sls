#!yamlscript
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# salt-halite
# -----------
# (Code-name) Halite is a Salt GUI. Status is pre-alpha.
# Contributions are very welcome. Join us in #salt on Freenode or on the salt-users mailing list.
#
# TODO:  Start it; not sure how to do it yet without using cmd
##

include: salt.certificates

$python: |
    from salt://salt/map.sls import SaltMap
    installed_by_repo = not __salt__['cmd.retcode'](SaltMap.installed_by_repo)

salt-halite-dependencies:
  pkg.installed:
    - names:
      - gcc
      - $SaltMap.python_dev
      - $SaltMap.libevent_dev

salt-halite-pip-dependencies:
  pip.installed:
    - names:
      - CherryPy
      - gevent
      - wheel
      $if installed_by_repo:
        - require:
          - pkg: $SaltMap.salt_master
          - pkg: salt-halite-dependencies
      $else:
        - require:
          - pkg: salt-halite-dependencies
          - pip: salt

# Install development version from git
salt-halite:
  pip.installed:
    - name: "git+https://github.com/saltstack/halite.git#egg=halite"
    - no_deps: True # We satisfy deps already
    - use_wheel: True
    - upgrade: False
    - require:
      - pip: salt-halite-pip-dependencies
      - pkg: git

# halite configuration file
/etc/salt/master.d/halite.conf:
  file.managed:
    - source: salt://salt/files/halite.conf
    - user: root
    - group: root
    - mode: 640
    - watch_in:
      - service: salt-master
