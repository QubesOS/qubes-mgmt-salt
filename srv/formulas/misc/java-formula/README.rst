java
====

This state installs java to /opt and sets up the alternatives system to point
to the binaries under /opt. To use this state the java tarball(s) must be
downloaded manually and placed in the files directory.

Available states
================

.. contents::
    :local:

``java.server_jre``
-------------------

Install the Oracle Java server jre, the tarball must be named `server_jre.tgz`
and placed in the files directory.

``java.server_jdk``
-------------------

Install the Oracle Java jdk

Example Pillar
==============

You can specify the ``source``, ``source_hash``, and ``home`` in your `pillar` file, like so:

.. code-block:: yaml

    java:
      jre:
        source: http://java.com...
        source_hash: sha1=SHA1OFDOWNLOAD
        home: /usr/local
      jdk:
        source: http://java.com...
        source_hash: sha1=SHA1OFDOWNLOAD
