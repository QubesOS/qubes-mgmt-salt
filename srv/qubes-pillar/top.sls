# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

base:
  # === Common ================================================================
  '*':
    - gnupg
    - users
