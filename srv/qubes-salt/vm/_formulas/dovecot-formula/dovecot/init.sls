{% from "dovecot/map.jinja" import dovecot with context %}

{% if grains['os_family'] == 'Debian' %}

dovecot_packages:
  pkg.installed:
    - names:
{% for name in dovecot.packages %}
      - dovecot-{{ name }}
{% endfor %}
    - watch_in:
      - service: dovecot_service

/etc/dovecot/local.conf:
  file.managed:
    - contents: |
        {{ dovecot.config.local | indent(8) }}
    - backup: minion
    - watch_in:
      - service: dovecot_service
    - require:
      - pkg: dovecot_packages

{% for name in dovecot.config.dovecotext %}
/etc/dovecot/dovecot-{{ name }}.conf.ext:
  file.managed:
    - contents: |
        {{ dovecot.config.dovecotext[name] | indent(8) }}
    - backup: minion
    - watch_in:
      - service: dovecot_service
    - require:
      - pkg: dovecot_packages
{% endfor %}

{% for name in dovecot.config.conf %}
/etc/dovecot/conf.d/{{ name }}.conf:
  file.managed:
    - contents: |
        {{ dovecot.config.conf[name] | indent(8) }}
    - backup: minion
    - watch_in:
      - service: dovecot_service
    - require:
      - pkg: dovecot_packages
{% endfor %}

{% for name in dovecot.config.confext %}
/etc/dovecot/conf.d/{{ name }}.conf.ext:
  file.managed:
    - contents: |
        {{ dovecot.config.confext[name] | indent(8) }}
    - backup: minion
    - watch_in:
      - service: dovecot_service
    - require:
      - pkg: dovecot_packages
{% endfor %}

dovecot_service:
  service.running:
    - name: dovecot
    - watch:
      - file: /etc/dovecot/local.conf
      - pkg: dovecot_packages
    - require:
      - pkg: dovecot_packages
{% endif %}
