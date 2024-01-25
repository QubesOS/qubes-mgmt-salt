# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# 1) Intial Setup: sync any modules, etc
# --> qubesctl saltutil.sync_all
#
# 2) Initial Key Import:
# --> qubesctl state.sls gnupg
#
# 3) Highstate will execute all states
# --> qubesctl state.highstate
#
# 4) Highstate test mode only.  Note note all states seem to conform to test
#    mode and may apply state anyway.  Needs more testing to confirm or not!
# --> qubesctl state.highstate test=True
#
# 5) Show all enabled tops
# --> qubesctl state.show_top

#  NOTE: Any configuration data contained within this file will override
#        and cause conflicts with tops_d/* top configurations; therefore
#        create any custom tops within the tops_d directory.

{%- set default = {'base': {'*': ['topd']}}|yaml %}


# If static list of enabled tops is present in "tops.yaml", use it without
# using salt.top module (it may be not available while using salt-ssh)
{%- if "/srv/salt/tops.yaml"|is_text_file -%}
  {%- load_yaml as tops %}
    {%- include "tops.yaml" %}
  {%- endload %}
  {%- if not tops %}
    {%- set tops = [] %}
  {%- endif %}
  {%- from "top.jinja" import merge_tops -%}
  {%- set top = merge_tops(tops) -%}
# otherwise, try to use salt.top module if present
{%- elif salt.top is defined %}
  {%- set top = salt.top.get_top('salt://_tops', opts, saltenv=None)|yaml %}
  {#- set status = salt.top.status(show_full_context())|yaml #}
{%- endif %}

{{ top if top is defined else default }}
