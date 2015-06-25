# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

==========================
Qubes test state functions
==========================
'''

# Import python libs
import logging

# Salt libs
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a salt test.debug module exists
    '''
    return 'test.debug' in __salt__


def _state_action(_action, *varargs, **kwargs):
    '''
    '''
    try:
        status = __salt__[_action](*varargs, **kwargs)
    except (SaltInvocationError, CommandExecutionError), e:
        status = Status(retcode=1, stderr=e.message + '\n')
    return dict(status)


def debug(name, *varargs, **kwargs):
    '''
    Sets debug mode for all or specific states status
    '''
    return _state_action('test.debug', name, *varargs, **kwargs)
