# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

==========================
Qubes misc state functions
==========================
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
    return True


def _state_action(_action, *varargs, **kwargs):
    '''
    '''
    try:
        status = __salt__[_action](*varargs, **kwargs)
    except (SaltInvocationError, CommandExecutionError), e:
        status = Status(retcode=1, result=False, comment=e.message + '\n')
    return dict(status)


def create(name, comment, result=None):
    '''
    Used to show an alert message when a condition is met not to include a state.
    '''
    return dict(Status(name=name, result=result, comment=comment))
