{% from "linux-dev/map.jinja" import linux_dev_pkgs with context %}

linux-dev-pkgs:
  pkg.installed:
    - pkgs: {{ linux_dev_pkgs.pkgs|json }}

