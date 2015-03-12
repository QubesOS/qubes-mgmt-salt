ejabberd:
  pkg.installed: []
  service.running:
    - enable: True
    - watch:
      - pkg: ejabberd
  user:
    - present

ejabberd.yml:
  file.managed:
    - name: /etc/ejabberd/ejabberd.yml
    - source: salt://ejabberd/ejabberd.yml
    - user: root
    - group: ejabberd
    - mode: '0644'
    - template: jinja
    - watch_in:
      - service: ejabberd
    - require:
      - user: ejabberd
