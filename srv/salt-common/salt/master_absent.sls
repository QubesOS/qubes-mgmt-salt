##
# Disable salt-master
##

salt-master:
  service.dead:
    - name: salt-master
    - enable: False

# salt-master unit file
/etc/systemd/system/salt-master.service:
  file:
    - absent
