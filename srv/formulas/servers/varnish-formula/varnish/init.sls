{% from "varnish/map.jinja" import varnish with context %}


varnish:
  pkg.installed:
    - name: {{ varnish.pkg }}
    {% if varnish.version is defined %}
    - version: {{ varnish.version }}
    {% endif %}
  service.running:
    - name: {{ varnish.service }}
    - enable: True
    - reload: True
    - require:
      - pkg: varnish
