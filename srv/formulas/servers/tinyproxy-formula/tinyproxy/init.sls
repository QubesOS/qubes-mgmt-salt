{% from "tinyproxy/defaults.yaml" import rawmap with context %}
{%- set tinp = salt['grains.filter_by'](rawmap, grain='os', merge=salt['pillar.get']('tinyproxy')) %}

tinyproxy:
  pkg.installed:
    - name: {{ tinp.package }}
  service.running:
    - name: {{ tinp.service }}
    - enable: True
    - watch:
      - pkg: tinyproxy

tinyproxy_config:
  file.managed:
    - name: {{ tinp.config }}
    - template: jinja
    - source: salt://tinyproxy/tinyproxy.conf
    - watch_in:
      - service: tinyproxy
