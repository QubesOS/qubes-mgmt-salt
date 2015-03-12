# -*- coding: utf-8 -*-
'''
Renderer that verifies state and pillar files

This renderer requires the python-gnupg package. Be careful to install the
``python-gnupg`` package, not the ``gnupg`` package, or you will get errors.

To set things up, you will first need to generate import a public key.  On
your master, run:

.. code-block:: bash

    $ gpg --import --homedir /etc/salt/gpgkeys pubkey.gpg

.. code-block:: yaml

    renderer: verify | jinja | yaml
'''

import os
import salt.utils
try:
    import gnupg
    HAS_GPG = True
    if salt.utils.which('gpg') is None:
        HAS_GPG = False
except ImportError:
    HAS_GPG = False
import logging

from salt.exceptions import (SaltRenderError, CommandExecutionError)

log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'verify'


def __virtual__():
    '''
    Confine this module to gpg enabled systems
    '''
    if HAS_GPG:
        return __virtualname__
    return False


def render(data, saltenv='base', sls='', argline='', **kwargs):
    '''
    Verify state ot pillar file using detatched signature file with same
    name as state/pillar file with the additional '.asc' suffix
    '''
    # Verify signed file
    try:
        client = salt.fileclient.get_file_client(__opts__)
        state = client.get_state(sls, saltenv)
        signature_file = client.cache_file(state['source'] + '.asc', saltenv)
        verify = __salt__['gpg.verify'](signature_file)
        return data
    except CommandExecutionError, error:
        raise SaltRenderError('GPG validation failed: {0}'.format(error))
