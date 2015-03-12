===============
dovecot-formula
===============

A salt formula that installs and configures the dovecot IMAP server. It currently supports Debian
or Ubuntu layout of the dovecot configuration files in /etc. Dovecot packages must be specified (imapd is installed by
default if nothing is specified in pillar). Config file content (where needed) is stored in pillar (see pillar.example).

Config file to pillar mappings:
===============================

.. code::

  /etc/dovecot/local.conf in dovecot:config:local

e.g.:

.. code::

  /etc/dovecot/dovecot-ldap.conf.ext in dovecot:config:dovecotext:ldap
  /etc/dovecot/conf.d/auth-ldap.conf.ext in dovecot:config:confext:ldap
  /etc/dovecot/conf.d/10-ldap.conf in dovecot:config:conf:10-ldap


.. note::

Any help, suggestions if this works / how this works for other distributions are welcome.

Available states
================

.. contents::
    :local:

``dovecot``
------------

Installs and configures the dovecot package, and ensures that the associated dovecot service is running.
