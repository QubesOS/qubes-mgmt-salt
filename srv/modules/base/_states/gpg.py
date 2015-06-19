# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       python-gpg
:platform:      all

Implementation of gpg utilities
===============================

.. code-block:: yaml

    vim.sls.asc:
      gpg.verify
        - source: salt://vim/init.sls.asc
'''

# Import python libs
import logging

# Salt libs
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Salt + Qubes libs
from qubes_utils import Status

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    # XXX: May need better conditional here as it may pick up the salt gpg module
    return 'gpg.import_key' in __salt__


def _state_action(_action, *varargs, **kwargs):
    '''
    '''
    try:
        status = __salt__[_action](*varargs, **kwargs)
    except (SaltInvocationError, CommandExecutionError), e:
        status = Status(retcode=1, result=False, comment=e.message + '\n')
    return dict(status)


def import_key(*varargs, **kwargs):
    '''
    Imports a gpg key into Salt's home directory to be able to verify signed
    state files.
    '''
    return _state_action('gpg.import_key', *varargs, **kwargs)


def verify(*varargs, **kwargs):
    '''
    Verify a gpg key.
    '''
    return _state_action('gpg.verify', *varargs, **kwargs)
