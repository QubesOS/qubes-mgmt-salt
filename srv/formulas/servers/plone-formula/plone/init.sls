{% from "plone/map.jinja" import plone with context %}

plone_virtualenv_packages:
  pkg.installed:
    - pkgs:
{% for pkg in plone.pkgs %}
      - {{ pkg }}
{% endfor %}

plone_virtualenv:
  file.directory:
    - name: {{ plone.venv_location }}
    - makedirs: True
    - user: {{ plone.user }}
    - group: {{ plone.group }}
    - mode: 750
  virtualenv.managed:
    - name: {{ plone.venv_location }}
    - requirements: salt://plone/files/requirements.txt
    - user: {{ plone.user }}
    - require:
      - pkg: plone_virtualenv_packages

buildout_basefiles:
  file.recurse:
    - template: jinja
    - context:
      user: {{ plone.user }}
      adminuser: {{ plone.adminuser }}
      adminpass: {{ plone.adminpass }}
    - name: {{ plone.instance_location }}
    - source: salt://plone/files/base
    - user: {{ plone.user }}
    - group: {{ plone.group }}
    - include_empty: True
    - require_in:
      - cmd: bootstrap_plone
    - watch_in:
      - cmd: bootstrap_plone
      - cmd: buildout_plone

bootstrap_plone:
  cmd.wait:
    - name: {{ plone.venv_location }}/bin/python bootstrap.py
    - cwd: {{ plone.instance_location }}
    - user: {{ plone.user }}
    - require:
      - virtualenv: plone_virtualenv

buildout_plone:
  cmd.wait:
    - name: {{ plone.instance_location }}/bin/buildout
    - cwd: {{ plone.instance_location }}
    - user: {{ plone.user }}
    - watch:
      - cmd: bootstrap_plone
    - watch_in:
      - service: plone_service

init_plone:
  file.managed:
    - name: /etc/init.d/plone
    - source: salt://plone/files/plone.init.jinja
    - template: jinja
    - context:
        instancepath: {{ plone.instance_location }}
        instancename: {{ plone.instance_name }}
    - user: root
    - group: root
    - mode: 0755
    - watch_in:
      - service: plone_service

plone_service:
  service.running:
    - name: plone
    - enable: True
