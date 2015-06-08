##
# Disable salt-minion
##

salt-minion:
  service.dead:
    - name: salt-minion
    - enable: False

# salt-minion unit file
/etc/systemd/system/salt-minion.service:
  file:
    - absent
