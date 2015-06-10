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


=====
TODO:
=====

States and functions to implement (qvm-commands):

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

# Import python libs
import sys
import collections
import logging

# Salt libs
from salt.output import nested
from salt.utils.odict import OrderedDict as _OrderedDict

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    return 'qvm.prefs' in __salt__


def _nested_output(obj):
    '''
    Serialize obj and format for output.
    '''
    nested.__opts__ = __opts__
    ret = nested.output(obj).rstrip()
    return ret


def _state_action(_action, *varargs, **kwargs):
    '''
    Calls the salt state via the state_utils utility function of same name.
    '''
    # Use loaded module since it will contain __opts__ and __salt__ dunders
    state_action = sys.modules['salt.loaded.ext.states.state_utils'].state_action
    return state_action(_action, *varargs, **kwargs)


def exists(name, *varargs, **kwargs):
    '''
    Returns True is vmname exists.
    '''
    varargs = list(varargs)
    varargs.append('exists')
    return _state_action('qvm.check', name, *varargs, **kwargs)


def absent(name, *varargs, **kwargs):
    '''
    Returns True is vmname is absent (does not exist).
    '''
    varargs = list(varargs)
    varargs.append('absent')
    return _state_action('qvm.check', name, *varargs, **kwargs)


def running(name, *varargs, **kwargs):
    '''
    Returns True is vmname is running.
    '''
    varargs = list(varargs)
    varargs.append('running')
    return _state_action('qvm.state', name, *varargs, **kwargs)


def halted(name, *varargs, **kwargs):
    '''
    Returns True is vmname is halted.
    '''
    varargs = list(varargs)
    varargs.append('halted')
    return _state_action('qvm.state', name, *varargs, **kwargs)


def start(name, *varargs, **kwargs):
    '''
    Start vmname (qvm-start).
    '''
    kwargs.setdefault('flags', [])
    kwargs['flags'].extend(['quiet', 'no-guid'])
    return _state_action('qvm.start', name, *varargs, **kwargs)


def shutdown(name, *varargs, **kwargs):
    '''
    Shutdown vmname (qvm-shutdown).
    '''
    kwargs.setdefault('flags', [])
    kwargs['flags'].append('wait')
    return _state_action('qvm.shutdown', name, *varargs, **kwargs)


def kill(name, *varargs, **kwargs):
    '''
    Kill vmname (qvm-kill).
    '''
    return _state_action('qvm.kill', name, *varargs, **kwargs)


def pause(name, *varargs, **kwargs):
    '''
    Pause vmname (qvm-pause).
    '''
    return _state_action('qvm.pause', name, *varargs, **kwargs)


def unpause(name, *varargs, **kwargs):
    '''
    Unpause vmname (qvm-unpause).
    '''
    return _state_action('qvm.unpause', name, *varargs, **kwargs)


def create(name, *varargs, **kwargs):
    '''
    Create vmname (qvm-create).
    '''
    return _state_action('qvm.create', name, *varargs, **kwargs)


def remove(name, *varargs, **kwargs):
    '''
    Remove vmname (qvm-remove).
    '''
    return _state_action('qvm.remove', name, *varargs, **kwargs)


def clone(name, source, *varargs, **kwargs):
    '''
    Clone a VM (qvm-clone).
    '''
    return _state_action('qvm.clone', source, name, *varargs, **kwargs)


def run(name, *varargs, **kwargs):
    '''
    Run command in virtual machine domain (qvm-run).
    '''
    return _state_action('qvm.run', name, *varargs, **kwargs)


def prefs(name, *varargs, **kwargs):
    '''
    Sets vmname preferences (qvm-prefs).
    '''
    return _state_action('qvm.prefs', name, *varargs, **kwargs)


def service(name, *varargs, **kwargs):
    '''
    Manage vmname service (qvm-service).
    '''
    return _state_action('qvm.service', name, *varargs, **kwargs)


def vm(name, *varargs, **kwargs):
    '''
    Wrapper to contain all VM state functions.

    State:

        exists
        absent

        create
        remove
        clone

        prefs
        service

    Power:

        running
        halted

        start
        shutdown
        kill
        pause
        unpause

        run
    '''
    def get_action(action):
        action_value = 'fail'
        if isinstance(action, collections.Mapping):
            action, action_value = action.items()[0]
        return action, action_value

    actions = [
        'exists',
        'running',
        'absent',
        'halted',
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
           'result': True,
           'comment': ''}

    if __opts__['test']:
        ret['result'] =  None

    # Action ordering from state file
    actions = kwargs.pop('actions', actions)

    # Store only the actions; no values
    _actions = []
    for action in actions:
        action, action_value = get_action(action)
        _actions.append(action)

    for action in kwargs.keys():
        if action not in _actions:
            ret['result'] = False
            ret['comment'] = 'Unknown action keyword: {0}'.format(action)
            return   ret

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
        action, action_value = get_action(action)

        if action in kwargs:
            # Parse kwargs and create varargs + keywords
            _varargs, keywords = parse_options(kwargs[action])

            # Execute action
            if ret['result'] or __opts__['test']:
                result = globals()[action](name, *_varargs, **keywords)
            else:
                linefeed = '\n\n' if ret['comment'] else ''
                ret['comment'] += '{0}====== [\'{1}\'] ======\n'.format(linefeed, action)
                ret['comment'] += '[SKIP] Skipping due to previous failure!'
                continue

            # Don't fail if action_value set to pass
            if not result['result'] and 'pass' not in action_value.lower():
                ret['result'] = result['result']

            if 'changes' in result and result['changes']:
                ret['changes']['qvm.' + action] = result['changes']

            if 'comment' in result and result['comment'].strip():
                linefeed = '\n\n' if ret['comment'] else ''
                ret['comment'] += '{0}====== [\'{1}\'] ======\n'.format(linefeed, action)
                ret['comment'] += result['comment']

    return ret
