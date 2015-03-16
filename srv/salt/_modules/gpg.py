# -*- coding: utf-8 -*-
'''
gnupg related utilities

Note:  Currently only implemented import key
'''

# Import python libs
import os
import re
import logging

import salt.utils
import salt.syspaths
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

try:
    import gnupg
    HAS_GPG = True
    if salt.utils.which('gpg') is None:
        HAS_GPG = False
except ImportError:
    HAS_GPG = False

log = logging.getLogger(__name__)
GPG_MESSAGE_HEADER = re.compile(r'-----BEGIN PGP MESSAGE-----')
GPG_SIGNED_MESSAGE_HEADER = re.compile(r'-----BEGIN PGP SIGNED MESSAGE-----')
DEFAULT_GPG_KEYDIR = os.path.join(salt.syspaths.CONFIG_DIR, 'gpgkeys')

# Define the module's virtual name
__virtualname__ = 'gpg'


def __virtual__():
    '''
    Confine this module to gpg enabled systems
    '''
    if HAS_GPG:
        return __virtualname__
    return False


def _get_homedir(homedir):
    if not HAS_GPG:
        raise SaltInvocationError('GPG unavailable. Install the python-gnupg package')
    if isinstance(__salt__, dict):
        if 'config.get' in __salt__:
            homedir = __salt__['config.get']('gpg_keydir', DEFAULT_GPG_KEYDIR)
        else:
            homedir = __opts__.get('gpg_keydir', DEFAULT_GPG_KEYDIR)
        log.debug('Reading GPG keys from: {0}'.format(homedir))

    return homedir


def _get_path(filename):
    if not filename:
        return ''
    client = salt.fileclient.get_file_client(__opts__)
    return client.cache_file(filename)


def _get_data(filename):
    try:
        with open(filename) as file_:
            return file_.read()
    except IOError, error:
        raise CommandExecutionError('Error reading: {0}. {1}'.format(filename,  error))


def import_key(key, homedir=None):
    '''
    Import a public key into gpg database.

    CLI Example:

    .. code-block:: bash

        salt '*' gpg.import_key
    '''
    homedir = _get_homedir(homedir)
    key = _get_path(key)

    if os.path.exists(key):
        gpg = gnupg.GPG(gnupghome=homedir)
        result = gpg.import_keys(_get_data(key))
        status = result.results[0]
        status['comment'] = result.stderr
        return status

    raise CommandExecutionError('GPG validation failed: invalid path {0}'.format(key))

def verify(signature_filename, data_filename=None, homedir=None):
    '''
    Verify a gpg signed file

    CLI Example:

    .. code-block:: bash

        salt '*' gpg.verify filename.sls.asc [data_filename] [homedir]
    '''
    homedir = _get_homedir(homedir)
    signature_filename = _get_path(signature_filename)

    if os.path.exists(signature_filename):
        gpg = gnupg.GPG(gnupghome=homedir)

        data_filename = _get_path(data_filename)
        if not data_filename:
            data_filename, ext = os.path.splitext(signature_filename)

        verify = gpg.verify_data(signature_filename, _get_data(data_filename))
        if verify.valid:
            return verify
        else:
            raise CommandExecutionError('GPG validation failed: {0}: {1}'.format(signature_filename, verify.status))
    raise CommandExecutionError('GPG validation failed: invalid path {0}'.format(signature_filename))
