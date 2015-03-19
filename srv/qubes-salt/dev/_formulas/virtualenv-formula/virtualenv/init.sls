{% from "virtualenv/package-map.jinja" import virtualenv with context %}

virtualenv:
  pkg.installed:
    - name: {{ virtualenv.pkg }}
