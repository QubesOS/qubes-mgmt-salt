{% from "sphinx_doc/map.jinja" import sphinx with context %}

include:
  - pip
  - virtualenv

{% set config = salt['pillar.get']('sphinx_doc', {}) %}

{% if 'venv' in config %}
sphinx_venv_dir:
  file.directory:
    - name: {{ config.venv }}
    - makedirs: True

sphinx_venv:
  virtualenv.managed:
    - name: {{ config.venv }}
    - require:
      - pkg: virtualenv
      - file: sphinx_venv_dir
  pip.installed:
    - name: {{ sphinx.pip_pkg }}
    - bin_env: {{ config.venv }}
    - require:
      - file: sphinx_venv_dir
      - virtualenv: sphinx_venv
{% endif %}
