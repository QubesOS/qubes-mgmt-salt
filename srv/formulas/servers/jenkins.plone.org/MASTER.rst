VIEW CONFIGURATION
------------------

Core (Plone 4.2/4.3 - Python 2.6/2.7)::

  + Column Testresult

Packages::

  Use a regular expression to include jobs into the view: Checked
  Regular expression: ^plone\..*|^Products.*

  Show standard Jenkins list at the top of the page: True

PLIPS:

  Use a regular expression to include jobs into the view: Checked
  Regular expression: ^PLIP.*|^plip.*

  Show standard Jenkins list at the top of the page: True

Pull Requests::

  Use a regular expression to include jobs into the view: Checked
  Regular expression: ^pull-request.*

  Show standard Jenkins list at the top of the page: True


JENKINS CONFIGURATION
---------------------

Standard View: Core

Xvfb installation:

Name: default
Directory in which to find Xvfb executable: /usr/bin

