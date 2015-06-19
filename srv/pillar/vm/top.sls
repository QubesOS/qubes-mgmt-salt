# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Virtual machine pillar top.sls
# /srv/pillar/vm/top.sls
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

vm:
  # === Common ================================================================
  '*':
    - qubes.users
