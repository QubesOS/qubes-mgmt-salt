# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

===========================
Qubes qvm-* state functions
===========================

Salt can manage many Qubes settings via the qvm state module.

Management declarations are typically rather simple:

.. code-block:: yaml

    appvm:
      qvm.prefs
        - label: green
'''

# Import python libs
import logging
#import os
#import re
import collections

# Import salt libs
import salt.utils
from salt.output import nested
#from salt.utils import namespaced_function as _namespaced_function
from salt.utils.odict import OrderedDict as _OrderedDict
#from salt._compat import string_types
from salt.exceptions import (
    CommandExecutionError, MinionError, SaltInvocationError
)

from qubes_utils import _update

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    return 'qvm.get_prefs' in __salt__

'''
TODO:
=====

- Consider creating an additional state that will allow all vm related
  configurations to be within one state (qvm.vm)

- Functions to implement (qvm-commands):
  [ ] Not Implemented
  [X] Implemented
  [1-9] Next to Implement

  [ ] qvm-add-appvm       [X] qvm-create              [ ] qvm-ls                       [X] qvm-shutdown
  [ ] qvm-add-template    [ ] qvm-create-default-dvm  [ ] qvm-pci                      [X] qvm-start
  [ ] qvm-backup          [ ] qvm-firewall            [X] qvm-prefs                    [ ] qvm-sync-appmenus
  [ ] qvm-backup-restore  [ ] qvm-grow-private        [X] qvm-remove                   [ ] qvm-sync-clock
  [ ] qvm-block           [ ] qvm-grow-root           [ ] qvm-revert-template-changes  [ ] qvm-template-commit
  [X] qvm-check           [ ] qvm-init-storage        [X] qvm-run                      [ ] qvm-trim-template
  [X] qvm-clone           [X] qvm-kill                [X] qvm-service                  [ ] qvm-usb

  [X] qvm-pause
  [X] qvm-unpause
'''


def _nested_output(obj):
    '''
    Serialize obj and format for output
    '''
    nested.__opts__ = __opts__
    ret = nested.output(obj).rstrip()
    return ret


# XXX: rename to something more descriptive; used to get error code and output only
def _call_function(name, function, *varargs, **kwargs):
    ret = {'name': name,
           'stdout': '',
           'stderr': '',
           'retcode': 0,
           'changes': {},
          }

    result = __salt__[function](name, *varargs, **kwargs)
    ret.update(result)

    ret['comment'] = ret['stdout']

    if __opts__['test']:
        #ret['result'] = None
        ret['result'] = None if not ret['retcode'] else False
    else:
        ret['result'] = True if not ret['retcode'] else False
    return ret


#def clone(name, clone_name, *varargs, **kwargs):
def OLDclone(name, *varargs, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    args, fnargs = salt.utils.arg_lookup(__salt__['qvm.clone']).values()
    for key, value in kwargs.items():
        if key in fnargs:
            fnargs[key] = value

    # Support test mode only
    if __opts__['test'] == True:
        # Pre-check if create should succeed
        ret = _call_function(name, 'qvm.check')
        ret['result'] = not ret['result']
        if not ret['result']:
            return ret
        ret['result'] = None
        ret['comment'] = 'VM {0} will be cloned\n{1}'.format(name, _nested_output(fnargs))
        return ret

    #fnargs['clone_name'] = clone_name
    ret = _call_function(name, 'qvm.clone', *varargs, **fnargs)
    return ret


def service(name, *varargs, **kwargs):
    '''
    Manage vmname service (qvm-service)
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    stdout = stderr = ''
    services = []

    # Send as *varargs...
    # ===================
    for key, value in kwargs.items():
        try:
            qvm_service = [key]
            qvm_service.extend(__salt__['qvm.tolist'](value))
            result = _call_function(name, 'qvm.service', *qvm_service, **kwargs)
            # XXX: Don't send kwargs since varargs are being used instead -- handled in module now
            #result = _call_function(name, 'qvm.service', *qvm_service)
        #except CommandExecutionError, e:
        except (SaltInvocationError, CommandExecutionError), e:
            stderr += e.message + '\n'
            continue
        stderr += result['stderr']
        stdout += result['stdout']
        _update(ret, result, create=True, append=['cmd', 'stderr', 'stdout'])

    #===========================================================================
    # XXX:
    #
    # DO NOT DELETE KWARGS LOGIC BELOW UNTIL ALL TESTS WRITTEN AND COMMANDLINE
    # SALT-CALL MODE IS TESTED.  NEED TO MAKE SURE BEST WAY FOR BOTH YAML
    # AND SALT-CALL IS BEING USED.
    #
    # VARARGS ALLOWS SALT-CALL QVM.SERVICE <ACTION> <VALUE>
    #
    # -- INSTEAD OF -- (something like this?)
    #
    # SALT-CALL QVM.SERVICE ACTION=<ACTION> VALUE=<VALUE>
    #===========================================================================
    #
    # Send as **kwargs...
    # ===================
    #for key, value in kwargs.items():
    #     Send kwargs...
    #     services.append({'action' : key, 'service_names': value})
    #for qvm_service in services:
    #    try:
    #        Send kwargs...
    #        result = _call_function(name, 'qvm.service', **qvm_service)
    ##    except CommandExecutionError, e:
    #    except (SaltInvocationError, CommandExecutionError), e:
    #        stderr += e.message + '\n'
    #        continue
    #    stderr += result['stderr']
    #    stdout += result['stdout']
    #    _update(ret, result, create=True)

    if stderr:
        ret['result'] = False
        stderr = 'stderr:\n{0}'.format(stderr)
        if stdout:
            stderr += 'stdout:\n'
    ret['comment'] = stderr + stdout
    return ret


def _vm_action(name, action, *varargs, **kwargs):
    '''
    Start, shutdown, kill, pause, unpause, etc
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    stdout = stderr = ''

    try:
        result = _call_function(name, action, *varargs, **kwargs)
        stderr += result['stderr']
        stdout += result['stdout']
        _update(ret, result, create=True)
    except (SaltInvocationError, CommandExecutionError), e:
        stderr += e.message + '\n'

    if stderr:
        ret['result'] = False
        stderr = 'stderr:\n{0}'.format(stderr)
        if stdout:
            stderr += 'stdout:\n'
    ret['comment'] = stderr + stdout
    return ret

# ==============================================================================

def exists(name, *varargs, **kwargs):
    '''
    Returns True is vmname exists
    '''
    varargs = list(varargs)
    varargs.append('exists')
    return _vm_action(name, 'qvm.check', *varargs, **kwargs)

def absent(name, *varargs, **kwargs):
    '''
    Returns True is vmname is absent (does not exist)
    '''
    varargs = list(varargs)
    varargs.append('absent')
    return _vm_action(name, 'qvm.check', *varargs, **kwargs)

def running(name, *varargs, **kwargs):
    '''
    Returns True is vmname is running
    '''
    varargs = list(varargs)
    varargs.append('running')
    return _vm_action(name, 'qvm.state', *varargs, **kwargs)

def dead(name, *varargs, **kwargs):
    '''
    Returns True is vmname is halted
    '''
    varargs = list(varargs)
    varargs.append('dead')
    return _vm_action(name, 'qvm.state', *varargs, **kwargs)

def create(name, *varargs, **kwargs):
    '''
    Create vmname (qvm-create)
    '''
    #kwargs['flags'] = ['quiet']
    return _vm_action(name, 'qvm.create', *varargs, **kwargs)

def remove(name, *varargs, **kwargs):
    '''
    Remove vmname (qvm-remove)
    '''
    return _vm_action(name, 'qvm.remove', *varargs, **kwargs)

def clone(name, target, *varargs, **kwargs):
    '''
    Clone a VM (qvm-clone)
    '''
    return _vm_action(name, 'qvm.clone', target, *varargs, **kwargs)

def start(name, *varargs, **kwargs):
    '''
    Start vmname (qvm-start)
    '''
    kwargs['flags'] = ['quiet']
    kwargs['flags'] = ['no-guid']
    return _vm_action(name, 'qvm.start', *varargs, **kwargs)


def shutdown(name, *varargs, **kwargs):
    '''
    Shutdown vmname (qvm-shutdown)
    '''
    kwargs['flags'] = ['wait']
    return _vm_action(name, 'qvm.shutdown', *varargs, **kwargs)


def kill(name, *varargs, **kwargs):
    '''
    Kill vmname (qvm-kill)
    '''
    return _vm_action(name, 'qvm.kill', *varargs, **kwargs)


def pause(name, *varargs, **kwargs):
    '''
    Pause vmname (qvm-pause)
    '''
    return _vm_action(name, 'qvm.pause', *varargs, **kwargs)


def unpause(name, *varargs, **kwargs):
    '''
    Unpause vmname (qvm-unpause)
    '''
    return _vm_action(name, 'qvm.unpause', *varargs, **kwargs)


def prefs(name, *varargs, **kwargs):
    '''
    Sets vmname preferences (qvm-prefs)
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    # Support test mode only
    if __opts__['test'] == True:
        current_state = __salt__['qvm.get_prefs'](name)
        data = dict([(key, value) for key, value in kwargs.items() if value != current_state.get(key, object)])
        ret['result'] = None
        ret['comment'] = 'The following preferences will be changed:\n{0}'.format(_nested_output(data))
        return ret

    ret = _call_function(name, 'qvm.prefs', *varargs, **kwargs)
    return ret


def run(name, *varargs, **kwargs):
    '''
    Run command in virtual machine domain (qvm-run)
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    # Support test mode only
    #if __opts__['test'] == True:
    #    current_state = __salt__['qvm.get_prefs'](name)
    #    data = dict([(key, value) for key, value in kwargs.items() if value != current_state[key]])
    #    ret['result'] = None
    #    ret['comment'] = 'The following preferences will be changed:\n{0}'.format(_nested_output(data))
    #    return ret

    ret = _call_function(name, 'qvm.run', *varargs, **kwargs)
    return ret


def vm(name, *varargs, **kwargs):
    '''
    Wrapper to contain all VM state functions

    create, remove, clone
    prefs, service
    exists, running, absent, dead
    start, stop, pause, unpause
    '''
    actions = [
        'exists',
        'running',
        'absent',
        'dead',
        'remove',
        'create',
        'clone',
        'prefs',
        'service',
        'unpause',
        'pause',
        'shutdown',
        'kill',
        'start',
        'run',
    ]

    ret = {'name': name,
           'changes': {},
           'result': None,
           'comment': ''}

    stdout = stderr = ''
    test = __opts__['test']

    #def to_dict(alist):
    #    return reduce(lambda r, d: r.update(d) or r, alist, {})

    def parse_options(options):
        varargs = []
        keywords = _OrderedDict()
        for option in options:
            if isinstance(option, collections.Mapping):
                keywords.update(option)
            else:
                varargs.append(option)
        return varargs, keywords

    for index, action in enumerate(actions):
        if action in kwargs:
            # Set default to True; it will be reset to False on any fail
            if ret['result'] is None:
                ret['result'] = True

            ##result = globals()[action](name, **to_dict(kwargs[action]))
            _varargs, keywords = parse_options(kwargs[action])
            result = globals()[action](name, *_varargs, **keywords)

            if 'changes' in result and result['changes']:
                ret['changes'].update(result['changes'])

            if 'result' in result and not result['result'] and result['result'] is not None:
                # Record failure
                ret['result'] = False

                try:
                    stderr += '=== \'{0}\' {1} ===\n'.format(action, result['retcode'])
                except KeyError:
                    stderr += '=== \'{0}\' {1} ===\n'.format(action, result['result'])

                # Switch to test mode for remainder of action items since we do
                # not want them to execute but may find the results useful
                __opts__['test'] =  True

            message = None
            if 'stderr' in result and result['stderr'].strip():
                stderr += '=== \'{0}\' stderr ===\n'.format(action)
                stderr += result['stderr'] + '\n'
                message = True

            if 'stdout' in result and result['stdout'].strip():
                stdout += '=== \'{0}\' stdout ===\n'.format(action)
                stdout += result['stdout'] + '\n'
                message = True

            if not message:
                if 'cmd' in result and result['cmd']:
                    stdout += '=== \'{0}\' {1} ===\n{2}\n'.format(action, result['result'], result['cmd'])

            if stdout and index < len(actions):
                stdout += '\n'

    # Reset test back to original selected mode if it was modified
    if test != __opts__['test']:
        __opts__['test'] = test

    #if not __opts__['test'] and ret['result'] is None:
    #    ret['result'] = False

    # If result is still None; and no tests are running, nothing was run
    if __opts__['test'] == True:
        ret['result'] = None
    elif ret['result'] is None:
        ret['result'] = False

    if stderr:
        stderr = 'stderr:\n{0}'.format(stderr)
        if stdout:
            stderr += 'stdout:\n'
    ret['comment'] = stderr + stdout
    if not ret['comment']:
        ret['comment'] = '{0}: {1}'.format(name, kwargs)

    return ret
