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
import sys
import logging

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    return 'test.debug' in __salt__


def _state_action(_action, *varargs, **kwargs):
    '''
    Calls the salt state via the state_utils utility function of same name.
    '''
    # Use loaded module since it will contain __opts__ and __salt__ dunders
    state_action = sys.modules['salt.loaded.ext.states.state_utils'].state_action
    return state_action(_action, *varargs, **kwargs)


def debug(name, *varargs, **kwargs):
    '''
    Sets debug mode for all or specific states results
    '''
    return _state_action('test.debug', name, *varargs, **kwargs)
