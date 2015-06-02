# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

===============
State Utilities
===============
'''

# Import python libs
import logging

# Salt libs
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Salt + Qubes libs
from qubes_utils import update

# Enable logging
log = logging.getLogger(__name__)


def state_action(_action, *varargs, **kwargs):
    '''
    State utility to standardize calling Qubes modules.

    Python State Example:

    .. code-block:: python

        from qubes_state_utils import state_action as _state_action

        def exists(name, *varargs, **kwargs):
            varargs = list(varargs)
            varargs.append('exists')
            return _state_action('qvm.check', name, *varargs, **kwargs)
    '''
    stdout = stderr = ''
    ret = {'name': '',
           'retcode': 0,
           'result': False,
           'comment': '',
           'changes': {},
           'stdout': '',
           'stderr': '',
          }

    try:
        result = __salt__[_action](*varargs, **kwargs)
        stderr += result['stderr']
        stdout += result['stdout']
        update(ret, result, create=True)
    except (SaltInvocationError, CommandExecutionError), e:
        ret['retcode'] = 1
        stderr += e.message + '\n'

    if not ret['comment']:
        if stderr:
            #ret['result'] = False
            if stdout:
                stdout = '====== stdout ======\n{0}\n\n'.format(stdout)
            stderr = '====== stderr ======\n{0}'.format(stderr)
        ret['comment'] = stdout + stderr

    if __opts__['test']:
        ret['result'] = None if not ret['retcode'] else False
    else:
        ret['result'] = True if not ret['retcode'] else False

    return ret
