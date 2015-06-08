{% from "dhcpd/map.jinja" import dhcpd with context %}

dhcpd:
  pkg.installed:
    - name: {{ dhcpd.server }}
  service.running:
    - name: {{ dhcpd.service }}
    - enable: True
    - require:
      - pkg: dhcpd
