# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Pillar top.sls
# /srv/pillar/top.sls
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

{%- set default = {'base': {'*': ['topd']}}|yaml(False) %}

{%- if salt.topd is defined %}
  {%- set top = salt.topd.get_top('salt://_topd', opts)|yaml(False) %}
  {#- set status = salt.topd.status(show_full_context())|yaml(False) #}
{%- endif %}

{{ top if top is defined else default }}
