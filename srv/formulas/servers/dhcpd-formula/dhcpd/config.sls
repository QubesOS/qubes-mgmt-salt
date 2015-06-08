{% from "dhcpd/map.jinja" import dhcpd with context %}

include:
  - dhcpd

dhcpd.conf:
  file.managed:
    - name: {{ dhcpd.config }}
    - source: salt://dhcpd/files/dhcpd.conf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
