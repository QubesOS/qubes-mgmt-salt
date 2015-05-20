#
# Qubes + Whonix Gateway Template Installation
#
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# sudo qubes-dom0-update --enablerepo=qubes-templates-community qubes-template-whonix-gw-experimental
qubes-template-whonix-gw-experimental:
  pkg.installed:
    - fromrepo: qubes-templates-community

# TODO: Abandon remaining tasks if one fails; Create comment to that effect
sys-whonix-test:
  qvm.vm:
    - remove: []
    - create:
      # options:
        # template: whonix-gw-experimental
        # label: purple
        # mem: 400
        # proxy
      - template: whonix-gw-experimental
      - label: purple
      - mem: 400
      - proxy
    - prefs:
      # TODO: Use a grain to determine release for proper firewall name
      - netvm: sys-firewall
      # timezone: UTC
      # TODO: Make this a pillar; maybe based on primary dom0 username?
      #       Umm; not for whonix; for other VM's
      - default_user: user
    - require:
      - pkg: qubes-template-whonix-gw-experimental

#whonix-gw-experimental:
#  qvm.vm:
#    - prefs:
#      - netvm: sys-whonix-test
#      # timezone: UTC
#      - default_user: user
#    #- require:
#    #  pkg: qubes-template-whonix-gw-experimental
