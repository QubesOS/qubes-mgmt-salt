A yamlscript to add users
=========================

Requirements
------------
- salt git develop version is required to run Yamlscript or any version > salt 2014.1.0-6384-g45ed9ce
- yamlscript (https://github.com/DockerNAS/yamlscript-formula)

Installation
------------
- Checkout out http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html to find out how to install formulas.

.. code-block:: yaml

  file_roots:
    base:
      - /srv/salt
      - /srv/salt-formulas/yamlscript-formula
      - /srv/salt-formulas/users-yamlscript-formula


- add ``users`` to /srv/salt/top.sls file:

.. code-block:: yaml

  base:
    '*':
      - users


Take a look at the example code in pillar in order to get an idea of the
required format to create user data and create a pillar file in
``/srv/pillar/users/init.sls``

Also add ``users`` to /srv/pillar/top.sls file:

.. code-block:: yaml

  base:
    '*':
      - users

