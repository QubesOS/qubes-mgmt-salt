# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# dom0 pillar top.sls
# /srv/pillar/dom0/top.sls
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

dom0:
  # === Dom0 ==================================================================
  'virtual:Qubes':
    - match: grain

    - qubes
    # qubes.users
    - qubes.virtual-machines
