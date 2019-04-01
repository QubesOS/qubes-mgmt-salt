# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Pillar top.sls
# /srv/pillar/top.sls
#
# Re-sync pillars
# --> qubesctl saltutil.refresh_pillar
#

{%- set default = {'base': {'*': ['topd.config']}}|yaml(False) %}

{%- if salt.top is defined %}
  {%- set top = salt.top.get_top('salt://_tops', opts, pillar=True, saltenv=None)|yaml(False) %}
  {#- set status = salt.top.status(show_full_context())|yaml(False) #}
{%- endif %}

{{ top if top is defined else default }}
