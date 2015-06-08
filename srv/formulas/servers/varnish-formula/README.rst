===============
varnish-formula
===============

A simple saltstack formula to install and configure Varnish.

This formula has been developed distributing id and state declarations in
different files to make it usable in most situations. It should be useful in
scenarios ranging from a simple install of the packages (without any special
configuration) to a more complex set-up.

General customization strategies
================================

* **Use pillar data**. This is the absolutely recommended way to use the
  formula. In most occassions all you need is to fill some of the key-values
  shown in the ``pillar.example`` file. If you feel that a certain value
  should be there then don't hesitate to propose an enhancement.

* Use the ``extra_conf`` key that in some cases is present in the pillar to add
  arbitrary configuration lines in the templates provided. This is a way to have
  a better customization without over-populating the pillar with new key-values.

* Add new subdirectories under ``files`` in addition to ``default``. This
  new subdirectories will contain different files to be used in certain
  conditions. This selection mechanism is based by default in the ``ìd`` grain
  of the minion (i.e. if there's a new subdirectory named ``minion01`` then
  the formula is going to look there first for that minion). This selection
  behavior can be extended to make it depend on any sorted list of grains,
  defined by the key ``files_switch``.

  For example, let's define in pillar something like:

  .. code:: yaml

      formula-name:
        files_switch: ['id', 'os_family']

  Let's have this ``files`` directory structure:

  .. code:: asciidoc

      files
        |-- minion01
        |       `-- etc
        |            `-- foo.conf.jinja
        |-- Debian
        |       `-- etc
        |            `-- foo.conf.jinja
        `-- default
                |-- etc
                |    |-- foo.conf.jinja
                |    `-- bar.conf.jinja
                `-- usr/share/thingy/*

  With this, we have the following:

  * if the minion id is ``minion01`` then ``files/minion01/etc/foo.conf.jinja``
    is going to be used

  * else if the minion os_family is ``Debian`` then
    ``files/Debian/etc/foo.conf.jinja`` is going to be used

  * else ``files/default/etc/foo.conf.jinja`` is going to be used

  Beware: **this is not designed to substitute pillar data**. Remember that
  pillar has to be used for information that it's essential to be only known for
  a certain set of minions (i.e. passwords, private keys and such).

* As a last resort you can actually fork the formula to suit your needs, keeping
  an eye for further improvements to merge into yours. Of course any pull-
  request that you can bring back it would be taken in account ;-)

.. note::

    Currently this formula supports Debian and RedHat os_family.

    See the full `Salt Formulas
    <http://docs.saltstack.com/en/latest/topics/development/conventions/formulas.html>`_ doc.

Available states
================

.. contents::
    :local:

``varnish``
-----------

Installs the varnish package, and starts the associated varnish service.

``varnish.conf``
----------------

Configures the varnish package.

``varnish.repo``
----------------

Adds the varnish official repositories.
