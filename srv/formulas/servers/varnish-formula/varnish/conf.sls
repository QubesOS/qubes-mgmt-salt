{% from "varnish/map.jinja" import varnish with context %}


include:
  - varnish


{% set files_switch = salt['pillar.get']('varnish:files_switch', ['id']) %}


# This state ID is going to have just a "require" instead of a "watch"
# statement because of:
#
# a) the varnish service is defined as reload=true and to actually apply changes
#    in this config file it's necessary a restart
# b) restart is potentially dangerous because it deletes the cache, so it's
#    preferrable to trigger an explicit and controlled restart after changing
#    this file
#
# As you probably know, to run a restart of the service you could use something
# like: salt 'varnish-node*' service.varnish restart.
{{ varnish.config }}:
  file:
    - managed
    - source:
      {% for grain in files_switch if salt['grains.get'](grain) is defined -%}
      - salt://varnish/files/{{ salt['grains.get'](grain) }}/etc/default/varnish.jinja
      {% endfor -%}
      - salt://varnish/files/default/etc/default/varnish.jinja
    - template: jinja
    - require:
      - pkg: varnish
    - require_in:
      - service: varnish


# Below we deploy the vcl files and we trigger a reload of varnish
{% for file in salt['pillar.get']('varnish:vcl:files', ['default.vcl']) %}
/etc/varnish/{{ file }}:
  file:
    - managed
    - source:
      {% for grain in files_switch if salt['grains.get'](grain) is defined -%}
      - salt://varnish/files/{{ salt['grains.get'](grain) }}/etc/varnish/{{ file }}.jinja
      {% endfor -%}
      - salt://varnish/files/default/etc/varnish/{{ file }}.jinja
    - template: jinja
    - require:
      - pkg: varnish
    - watch_in:
      - service: varnish
{% endfor %}


# Below we delete the "absent" vcl files and we trigger a reload of varnish
{% for file in salt['pillar.get']('varnish:vcl:files_absent', []) %}
/etc/varnish/{{ file }}:
  file:
    - absent
    - require:
      - pkg: varnish
    - watch_in:
      - service: varnish
{% endfor %}
