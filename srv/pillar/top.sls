# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Common base pillar top.sls
# /srv/pillar/base/top.sls
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

base:
  # === Common ================================================================
  '*':
    - gnupg
  
  #vm_other:
    #vm_other:
      #- match: nodegroup
      #- misc

vm_other:
  '*':
    - misc

# # === Dom0 ==================================================================
# dom0:
#   - match: nodegroup
#   - qubes
#   # qubes.users
#   - qubes.virtual-machines

  # === Common ================================================================
# vm:
#   - match: nodegroup
#   - qubes.users

  # === Common ================================================================
# vm_other:
#   - match: nodegroup
#   - misc
