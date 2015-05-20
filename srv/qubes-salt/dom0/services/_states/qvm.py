# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

Implementation of Qubes qvm utilities
=====================================

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
  [X] qvm-check           [ ] qvm-init-storage        [3] qvm-run                      [ ] qvm-trim-template
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
        ret['result'] = None
    else:
        ret['result'] = True if not ret['retcode'] else False
    return ret


def _update(target, source, create=False, allowed=None, append=False):
    '''
    Updates the values of a nested dictionary of varying depth without over-
    writing the targets root nodes.

    target
        Target dictionary to update

    source
        Source dictionary that will be used to update `target`

    create
        if True then new keys can be created during update, otherwise they will be tossed
        if they do not exist in `target`.

    allowed
        list of allowed keys that can be created even if create is False

    append [True] or ['list_of_keys', 'key4']
        appends to strings or lists if append is True or key in list
    '''
    if not allowed:
        allowed = []

    for key, value in source.items():
        if isinstance(value, collections.Mapping):
            if key in target.keys() or create or key in allowed:
                replace = _update(target.get(key, {}), value, create=create)
                target[key] = replace
        else:
            if key in target.keys() or create or key in allowed:
                if append and (append is True or key in append):
                    if isinstance(source[key], str) and isinstance(target.get(key, ''), str):
                        target.setdefault(key, '')
                        target[key] += source[key]
                    elif isinstance(source[key], list) and isinstance(target.get(key, []), list):
                        target.setdefault(key, [])
                        target[key].extend(source[key])
                    else:
                        target[key] = source[key]
                else:
                    target[key] = source[key]
    return target


def check(name, *varargs, **kwargs):
    '''
    Returns True is vmname exists
    '''
    ret = _call_function(name, 'qvm.check', *varargs, **kwargs)
    return ret


def missing(name, *varargs, **kwargs):
    '''
    Returns True is vmname does not exist
    '''
    ret = _call_function(name, 'qvm.check', *varargs, **kwargs)
    ret['result'] = not ret['result']
    return ret


def running(name, *varargs, **kwargs):
    '''
    Returns True is vmname is running, False if not
    '''
    ret = _call_function(name, 'qvm.state', *varargs, **kwargs)
    return ret


def dead(name, *varargs, **kwargs):
    '''
    Returns True is vmname is halted
    '''
    ret = _call_function(name, 'qvm.state', *varargs, **kwargs)
    ret['result'] = not ret['result']
    return ret


#def OLDcreate(name, **kwargs):
#    '''
#    '''
#    ret = {'name': name,
#           'changes': {},
#           'result': False,
#           'comment': ''}
#
#    args, fnargs = salt.utils.arg_lookup(__salt__['qvm.create']).values()
#    for key, value in kwargs.items():
#        if key in fnargs:
#            fnargs[key] = value
#
#    # Support test mode only
#    if __opts__['test'] == True:
#        # Pre-check if create should succeed
#        ret = _call_function(name, 'qvm.check')
#        ret['result'] = not ret['result']
#        if not ret['result']:
#            return ret
#        ret['result'] = None
#        ret['comment'] = 'VM {0} will be created\n{1}'.format(name, _nested_output(fnargs))
#        return ret
#
#    ret = _call_function(name, 'qvm.create', **fnargs)
#    return ret


def remove(name, *varargs, **kwargs):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    args, fnargs = salt.utils.arg_lookup(__salt__['qvm.remove']).values()
    for key, value in kwargs.items():
        if key in fnargs:
            fnargs[key] = value

    # Support test mode only
    if __opts__['test'] == True:
        # Pre-check if create should succeed
        ret = _call_function(name, 'qvm.check')
        if not ret['result']:
            return ret
        ret['result'] = None
        ret['comment'] = 'VM {0} will be removed\n{1}'.format(name, _nested_output(fnargs))
        return ret

    ret = _call_function(name, 'qvm.remove', *varargs, **fnargs)
    return ret


def clone(name, target, *varargs, **kwargs):
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

    fnargs['target'] = target
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
        except CommandExecutionError, e:
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
    #    except CommandExecutionError, e:
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
    except CommandExecutionError, e:
        stderr += e.message + '\n'

    if stderr:
        ret['result'] = False
        stderr = 'stderr:\n{0}'.format(stderr)
        if stdout:
            stderr += 'stdout:\n'
    ret['comment'] = stderr + stdout
    return ret

# ==============================================================================
# ==============================================================================
# ==============================================================================
#
# TODO:
# -----
# - Seperate out varargs, like proxy; send them as varargs; kwargs as keywords
# - Test with command line salt-call to make sure we can also send varargs
# - How can we enter these varargs in sls state with WITHOUT creating 'options'
#
#    - Seems like I can't with standalone sls; but can with qvm.vm.
#    - May be able to modify yamlscript to allow syntax and not be confused
#      with salt thinking multiple functions are defined
#    - IS THERE A BETTER TERM THAN 'OPTIONS' for the OPTIONAL args?
#
# ==============================================================================
# ==============================================================================
# ==============================================================================
#def create(name, **kwargs):
def create(name, *varargs, **kwargs):
    '''
    Create vmname (qvm-create)
    '''
    ##kwargs['options'] = ['quiet']
    #return _vm_action(name, **kwargs)
    return _vm_action(name, 'qvm.create', *varargs, **kwargs)

def OLDcreate_maybe(name, *varargs, **kwargs):
    #ret = {'name': name,
    #       'changes': {},
    #       'result': False,
    #       'comment': ''}

    #args, fnargs = salt.utils.arg_lookup(__salt__['qvm.create']).values()
    #for key, value in kwargs.items():
    #    if key in fnargs:
    #        fnargs[key] = value

    # Support test mode only
    #if __opts__['test'] == True:
    #    # Pre-check if create should succeed
    #    ret = _call_function(name, 'qvm.check')
    #    ret['result'] = not ret['result']
    #    if not ret['result']:
    #        return ret
    #    ret['result'] = None
    #    ret['comment'] = 'VM {0} will be created\n{1}'.format(name, _nested_output(fnargs))
    #    return ret

    # XXX: CONFIRM test mode is actually supported!
    # qvm.create supports test mode within function module
    result = _call_function(name, 'qvm.create', *varargs, **kwargs)
    return result


def start(name, *varargs, **kwargs):
    '''
    Start vmname (qvm-start)
    '''
    kwargs['options'] = ['quiet']
    kwargs['options'] = ['no-guid']
    return _vm_action(name, 'qvm.start', *varargs, **kwargs)


def shutdown(name, *varargs, **kwargs):
    '''
    Shutdown vmname (qvm-shutdown)
    '''
    return _vm_action(name, 'qvm.shutdown', *varargs, **kwargs)


def kill(name, *varargs, **kwargs):
    '''
    Kill vmname (qvm-kill)
    '''
    kwargs['options'] = ['kill']
    return _vm_action(name, 'qvm.shutdown', *varargs, **kwargs)


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
    check, running, missing, dead
    start, stop, pause, unpause
    '''
    actions = [
        'check',
        'running',
        'missing',
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
