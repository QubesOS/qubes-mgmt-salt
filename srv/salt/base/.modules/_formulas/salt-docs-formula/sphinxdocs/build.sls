{% macro builddocs(doc, version, format, repo, src_dir, doc_dir, build_dir,
    clean=False, force=False, fire_event=True, push_files=True) %}

{% set build_dir = build_dir.format(version=version) %}
{% set id_prefix = '_'.join([doc, format, version]) %}
{% set venv = salt.pillar.get('sphinx_doc:venv') %}

# Make any parent directories needed for the clone directory.
'{{ doc }}_src_dir':
  file:
    - directory
    - name: {{ src_dir }}
    - makedirs: True

# Clone the respository.
'{{ doc }}_repo':
  git:
    - latest
    - name: {{ repo }}
    - rev: {{ version }}
    - target: {{ src_dir }}
    - require:
      - pkg: git
      - file: {{ doc }}_src_dir

# Optionally run the clean routines before running a new build.
{% if clean %}
'{{ id_prefix }}_cleandocs':
  cmd:
    - run
    - name: |
        make clean SPHINXOPTS='-q' BUILDDIR={{ build_dir }} \
            SPHINXBUILD={{ venv }}/bin/sphinx-build 2>/dev/null || true
    - cwd: {{ doc_dir }}
    - require_in:
      - cmd: {{ id_prefix }}_builddocs
{% endif %}

# Build the docs.
'{{ id_prefix }}_builddocs':
  cmd:
    - {{ 'run' if (clean or force) else 'wait' }}
    - name: |
        make {{ format }} SPHINXOPTS='-q' BUILDDIR={{ build_dir }} \
            SPHINXBUILD={{ venv }}/bin/sphinx-build \
            LATEXOPTS="-interaction=nonstopmode"
    - cwd: {{ doc_dir }}
    - watch:
      - git: {{ doc }}_repo

# Push the build up to the master.
{% if push_files %}
'{{ id_prefix }}_push_build':
  module:
    - run
    - name: cp.push_dir
    - path: {{ build_dir }}/{{ format }}
    - onchanges:
      - cmd: '{{ id_prefix }}_builddocs'
{% endif %}

# Signal any interested parties that the build is ready.
{% if fire_event %}
'{{ id_prefix }}_build_finished':
  event:
    - fire_master
    - name: sphinxdocs/build/finished
    - data:
        doc: {{ doc }}
        version: '{{ version }}'
        format: {{ format }}
        build_dir: {{ build_dir }}
        build: {{ build_dir }}/{{ format }}
    - onchanges:
      - module: '{{ id_prefix }}_push_build'
{% endif %}

{% endmacro %}


{% set build = salt.pillar.get('sphinxdocs:build') %}
{% if build %}
{% import_yaml "sphinxdocs/defaults.yaml" as defaults %}
{% set conf = defaults.sphinxdocs.docs[build.doc] %}

include:
  - git
  - sphinx_doc.venv
  {% if 'latex' in build.format %}
  - latex
  {% endif %}
  {% if 'xetex' in build.format %}
  - latex
  - latex.xetex
  {% endif %}

{% if 'xetex' in build.format %}
dejavu-fonts:
  pkg:
    - installed
    - pkgs:
      - dejavu-sans-fonts
      - dejavu-sans-mono-fonts
      - dejavu-serif-fonts
{% endif %}

{{ builddocs(build.doc, build.version, build.format, conf.repo, conf.src_dir,
    conf.doc_dir, conf.build_dir, build.get('clean'), build.get('force')) }}

{% endif %}
