# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# 1) Intial Setup: sync any modules, etc
# --> qubesctl saltutil.sync_all
#
# 2) Initial Key Import:
# --> qubesctl state.sls gpg
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

{%- set default = {'base': {'*': ['topd']}}|yaml(False) %}

{%- if salt.topd is defined %}
  {%- set top = salt.topd.get_top('salt://_tops', opts, saltenv=None)|yaml(False) %}
  {#- set status = salt.topd.status(show_full_context())|yaml(False) #}
{%- endif %}

{{ top if top is defined else default }}
