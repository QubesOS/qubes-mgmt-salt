=============
plone-formula
=============

This formula installs plone via buildout. The formula can be used either by forking or extending. When forking, the buildout.cfg in files/base can be adapted.
When buildout configuration is stored in i.e. a git repository, the plone formula can be extended and the buildout_basefiles state has to be overridden in the derived formula.

.. note::

Suggestions, bug reports and comments are welcome.

Available states
================

.. contents::
    :local:

``plone``
---------

Installs and configures plone virtualenv and instance from buildout. Requires plone user and group to be present.

``plone.user``
--------------

Ensures the presence of the specified plone user and group running the plone instance.

Extend example:
===============

::

    {% from "plone/map.jinja" import plone with context %}

    include:
      - plone

    extend:
      buildout_basefiles:
        file.absent:
          - name: /youdonotfindme

        git.latest:
          - name: gitolite@somehost:plone-buildout
          - target: {{ plone.instance_location }}
          - user: {{ plone.user }}
          - group: {{ plone.group }}
          - require_in:
            - cmd: bootstrap_plone
          - watch_in:
            - cmd: bootstrap_plone
            - cmd: buildout_plone

