{% import_yaml 'sphinxdocs/defaults.yaml' as defaults %}
{# TODO: use pillar.get() with merge arg to override via Pillar #}
{% set sphinxdocs = defaults['sphinxdocs'] %}

{% set app_dir = sphinxdocs.get('app_dir', '/var/sphinxdocs') %}

include:
  - cherrypy.pip

sphinxdocs_app:
  file:
    - managed
    - name: {{ app_dir }}/sphinxdocs.py
    - source: salt://sphinxdocs/sphinxdocs.py
    - makedirs: True

sphinxdocs_ini:
  file:
    - managed
    - name: /etc/sphinxdocs.ini
    - source: salt://sphinxdocs/files/sphinxdocs.ini
    - template: jinja
    - context:
        docs: {{ sphinxdocs.get('docs', {}) | json() }}
        config: {{ sphinxdocs.get('conf', {}) | json() }}

sphinxdocs_init:
  file:
    - managed
    - name: /etc/init.d/sphinxdocs
    - source: salt://sphinxdocs/files/sphinxdocs.init
    - template: jinja
    - mode: 0775
    - context:
        config: {{ sphinxdocs | json() }}

sphinxdocs_service:
  service:
    - running
    - name: sphinxdocs
    - enable: True
    - require:
      - file: sphinxdocs_init
      - pip: cherrypy_pip
    - watch:
      - file: sphinxdocs_ini

{% if grains['os_family'] in ['RedHat'] %}
sysconfig_iptables:
  file:
    - managed
    - name: /etc/sysconfig/iptables
    - contents: |
        *filter
        :INPUT ACCEPT [0:0]
        :FORWARD ACCEPT [0:0]
        :OUTPUT ACCEPT [0:0]
        -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
        -A INPUT -p icmp -j ACCEPT
        -A INPUT -i lo -j ACCEPT
        -A INPUT -m conntrack --ctstate NEW -m tcp -p tcp --dport 22 -j ACCEPT
        -A INPUT -m conntrack --ctstate NEW -m tcp -p tcp --dport {{ sphinxdocs.conf.global['server.socket_port'] }} -j ACCEPT
        -A INPUT -j REJECT --reject-with icmp-host-prohibited
        -A FORWARD -j REJECT --reject-with icmp-host-prohibited
        COMMIT

service_iptables:
  module:
    - wait
    - name: service.restart
    - m_name: iptables
    - watch:
      - file: sysconfig_iptables
{% endif %}
