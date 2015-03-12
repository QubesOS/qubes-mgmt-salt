{% from "cherrypy/map.jinja" import cherrypy with context %}

cherrypy:
  pkg:
    - installed
    - name: {{ cherrypy.pkg }}
