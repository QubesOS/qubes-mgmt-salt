/srv/salt/bootstrap/stable/bootstrap-salt.sh:
  file.managed:
    - source: https://raw.githubusercontent.com/saltstack/salt-bootstrap/stable/bootstrap-salt.sh
    - makedirs: True

/srv/salt/bootstrap/develop/bootstrap-salt.sh:
  file.managed:
    - source: https://raw.githubusercontent.com/saltstack/salt-bootstrap/develop/bootstrap-salt.sh
    - makedirs: True
