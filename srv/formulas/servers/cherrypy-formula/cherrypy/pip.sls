{% from "cherrypy/map.jinja" import cherrypy with context %}

include:
  - pip

cherrypy_pip:
  pip:
    - installed
    - name: {{ cherrypy.pip_pkg }}
