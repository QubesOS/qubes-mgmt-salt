##
# Disable salt-api
##

salt-api:
  service.dead:
    - name: salt-api
    - enable: False

# salt-api unit file
/etc/systemd/system/salt-api.service:
  file:
    - absent
