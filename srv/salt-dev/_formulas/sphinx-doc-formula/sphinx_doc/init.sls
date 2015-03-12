{% from "sphinx_doc/map.jinja" import sphinx with context %}

sphinx_doc:
  pkg.installed:
    - name: {{ sphinx.pkg }}
