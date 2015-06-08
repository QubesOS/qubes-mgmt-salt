{% set java = pillar.get('java', {}) -%}
{% set jdk  = java.get('jdk') -%}
{% set home = jdk.get('home', '/opt') -%}

server_jdk_tar:
  file.managed:
{%- if jdk['source'] is defined %}
    - name: {{ home }}/server_jdk.tgz
    - source: {{ jdk['source'] }}
    - source_hash: {{ jdk['source_hash'] }}
{% else -%}
    - name: {{ home }}/server_jdk.tgz
    - source: salt://java/files/server_jdk.tgz
{% endif -%}
  cmd.run:
    - name: tar xvf {{ home }}/server_jdk.tgz -C {{ home }}
    - require:
      - file: server_jdk_tar
