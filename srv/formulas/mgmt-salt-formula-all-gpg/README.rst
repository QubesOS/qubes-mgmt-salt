===============
gpg-formula
===============

Includes a custom gpg state, module and render.  The custom state and module provides the abiolity to import or verify
gpg keys, while the custom render will fail to render a .sls state file if the #!verify shebang is present and the
statefile fails verification do to any reason such as missing key, missing detached signature

Available states
================

.. contents::
    :local:

``gpg.import_key``
------------

Import a key from text or file

user
    Which user's keychain to access, defaults to user Salt is running as.
    Passing the user as 'salt' will set the GPG home directory to
    /etc/salt/gpgkeys.

contents
    The text containing import key to import.

contents-pillar
    The pillar id containing import key to import.

source
    The filename containing the key to import.

CLI Example:

.. code-block:: bash

    qubesctl gpg.import_key contents='-----BEGIN PGP PUBLIC KEY BLOCK-----
    ... -----END PGP PUBLIC KEY BLOCK-----'

    qubesctl gpg.import_key source='/path/to/public-key-file'

    qubesctl gpg.import_key contents-piller='gpg:gpgkeys'


``gpg.verify``
------------

Verify a message or file

source
    The filename.asc to verify.

key-content
    The text to verify.

data-source
    The filename data to verify.

user
    Which user's keychain to access, defaults to user Salt is running as.
    Passing the user as 'salt' will set the GPG home directory to
    /etc/salt/gpgkeys.

CLI Example:

.. code-block:: bash

    qubesctl gpg.verify source='/path/to/important.file.asc'

    qubesctl gpg.verify <source|key-content> [key-data] [user=]


``custom gpg renderer``
------------
Renderer that verifies state and pillar files

This renderer requires the python-gnupg package. Be careful to install the
``python-gnupg`` package, not the ``gnupg`` package, or you will get errors.

To set things up, you will first need to generate import a public key.  On
your master, run:

.. code-block:: bash

    $ gpg --import --homedir /etc/salt/gpgkeys pubkey.gpg

.. code-block:: yaml

    sls shebang: verify | jinja | yaml

