##
# Disable salt-syndic
##

salt-syndic:
  service.dead:
    - name: salt-syndic
    - enable: False

# salt-syndic unit file
/etc/systemd/system/salt-syndic.service:
  file:
    - absent
