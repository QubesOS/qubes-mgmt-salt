# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

============================
Qubes qvm-* modules for salt
============================        
'''

# Import python libs
import os
import subprocess
import copy
import inspect
import argparse
import logging
import collections

from inspect import getargvalues, stack

# Import salt libs
import salt.utils
from salt.utils import which as _which
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

from differ import DictDiffer, ListDiffer
from qubes_utils import _update

# Import Qubes libs
from qubes.qubes import QubesVmCollection

log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'qvm'

def __virtual__():
    '''
    Confine this module to Qubes dom0 based systems
    '''
    try:
        virtual_grain = __grains__['virtual'].lower()
        virtual_subtype = __grains__['virtual_subtype'].lower()
    except Exception:
        return False

    enabled = ('xen dom0')
    if virtual_grain == 'qubes' or virtual_subtype in enabled:
        return __virtualname__
    return False

#__outputter__ = {
#    'get_prefs': 'txt',
#}


# Used to identify values that have not been passed to functions which allows
# the function modules not to have to know anything about the default types
# excpected
try:
    if MARKER:
        pass
except NameError:
    MARKER = object()

import types
def _tostring(value):
    '''Convert value to string when possible (for argparse)
    '''
    if not value:
        value = ''
    elif isinstance(value, types.IntType):
        value = str(value)
    elif isinstance(value, types.ListType):
        value = ' '.join(value)

    return value


def _tolist(value):
    '''Converts value to a list.
    '''
    if not value:
        value = []
    elif isinstance(value, str):
        value = [value,]
    elif isinstance(value, tuple):
        value = list(value)
    return value


def arginfo(kwargs_list=None, argv_ordering=[], skip=[]):
    '''
    Returns dictionary of calling function's named arguments and values as well
    as option to put values from kwargs on argv stack to allow processing as
    optional vars. (add --before the values) and formats in requested ordering.

    kwargs_list: Provide a keys in list that are available in kwargs to place
                 treat those values as varargs
                 example:
                 ['flags'] - Any vaules contained in kwargs['flags'], will
                 be handled as varargs

    argv_ordering: Create alternate `argv` format
                 default:
                    ['varargs', 'keywords', 'args']
                 example:
                    ['varargs', 'keywords', 'args', 'cmd']

    skip:        Skip formatting for giving arg type;
                 example: ['varargs']
    '''
    frame = stack()[1][0]
    info = getargvalues(frame)._asdict()

    locals_ = info.pop('locals', {})
    info['__args'] = info.pop('args', None)
    info['__varargs'] = info.pop('varargs', None)
    info['__keywords'] = info.pop('keywords', None)
    info['_argparse_args'] = []
    info['_argparse_varargs'] = []
    info['_argparse_keywords'] = []
    info['_argparse_flags'] = []
    info['__argv'] = []

    # Convert varargs to a list if it exists so it can be appened to
    if info['__varargs'] in locals_:
        locals_[info['__varargs']] = _tolist(locals_[info['__varargs']])

    if kwargs_list and isinstance(kwargs_list, list) and info['__keywords'] and info['__keywords'] in locals_:
        for arg in kwargs_list:
            if arg not in locals_[info['__keywords']]:
                continue

            #if not isinstance(locals_[info['__keywords']][arg],  list):
            #    continue

            # Remove from locals_ stack and reference to kwarg_item
            kwargs_items = _tolist(locals_[info['__keywords']].pop(arg))

            # Make sure varargs objects exist
            #if not info['__varargs']:
            #    info['__varargs'] = ('varargs')
            #    locals_[info['__varargs']] = []

            # Make sure varargs is not a tuple
            #if isinstance(locals_[info['__varargs']], tuple):
            #    locals_[info['__varargs']] = list(locals_[info['__varargs']])

            # In salt, it in not possible to list a single keyword within the
            # root state, so module option flags need to be included in a list
            # and these values will then be placed on varargs stack so they
            # can be positioned and escaped
            for item in kwargs_items:
                if isinstance(item, str):
                    # Since these are not 'provided' varargs, they are treated
                    # as keywords for the purposes of skipping argparse
                    # formatting
                    #if 'keywords' in skip:
                    if 'flags' in skip:
                        #locals_[info['__varargs']].append(item)
                        info['_argparse_flags'].append(item)
                    else:
                        #locals_[info['__varargs']].append('--{0}'.format(item))
                        info['_argparse_flags'].append('--{0}'.format(item))
                elif isinstance(item, collections.Mapping):
                    for key, value in item.items():
                        locals_[key] = _tostring(value)
                        locals_[info['__keywords']][key] = _tostring(value)

    # Populate info with values from arginfo
    for arg_name in info['__args'] + [info['__varargs']] + [info['__keywords']]:
        if arg_name:
            info[arg_name] = locals_[arg_name]

    # args - positional argv
    if info['__args']:
        for name in info['__args']:
            # Get rid of any references to self
            if name ==  'self':
                continue
            info['_argparse_args'].append(_tostring(info[name]))

    # *varargs - positional argv
    if info['__varargs']:
        for name in _tolist(info[info['__varargs']]):
            # Ignore 'private' keywords
            if not name.startswith('__'):
                # Make keyword optional
                if 'varargs' in skip:
                    info['_argparse_varargs'].append(name)
                elif name.startswith('--'):
                    info['_argparse_varargs'].append(name)
                else:
                    info['_argparse_varargs'].append('--{0}'.format(name))

    # **kwargs = optional argv
    if info['__keywords']:
        for name, value in info[info['__keywords']].items():
            # Ignore 'private' keywords
            if not name.startswith('__'):
                # Make keyword optional
                if 'keywords' in skip or name.startswith('--'):
                    info['_argparse_keywords'].append(name)
                else:
                    info['_argparse_keywords'].append('--{0}'.format(name))

                if isinstance(value, list):
                    value = ' '.join(value)
                info['_argparse_keywords'].append(_tostring(value))

    if not argv_ordering:
        #argv_ordering = ['varargs', 'keywords', 'args']
        argv_ordering = ['flags', 'keywords', 'args', 'varargs']
    for section in argv_ordering:
        # '_argparse_keywords', 'vmname'
        section = '_argparse_{0}'.format(section)
        if section in info:
            if isinstance(info[section], list):
                info['__argv'].extend(info[section])
            else:
                info['__argv'].append(_tostring(info[section]))

        # 'self.cmd' in locals_['self']
        elif section.startswith('self.') and 'self' in locals_ and hasattr(locals_['self'], section[5:]):
            info['__argv'].append(_tostring(getattr(locals_['self'], section[5:])))

        # 'cmd' in locals_
        elif section in locals_:
            info['__argv'].append(_tostring(locals_[section]))

    return copy.deepcopy(info)


# XXX: Not yet used
def _get_fnargs(function, **kwargs):
    '''Returns all args that a function uses along with default values.
    '''
    args, fnargs = salt.utils.arg_lookup(function).values()
    for key, value in kwargs.items():
        if key in fnargs:
            fnargs[key] = value
    return fnargs


def _alias(new_name):
    '''
    Creates a generated class or function alias.

    Doc strings are also copied to wrapper so they are available to salt command
    line interface via the --doc option.
    '''
    def wrapper(func):
        # Class objects
        if hasattr(func, '__class__'):
            frame = stack()[0][0]
            func_globals = frame.f_globals
        # Functions
        else:
            func_globals = func.func_globals if hasattr(func, 'func_globals') else func.__globals__
        setattr(func, '__name__', new_name)
        setattr(func, '__doc__', func.__doc__)
        func_globals_save = {new_name: func}
        func_globals.update(func_globals_save)
        return func
    return wrapper


def _function_alias(new_name):
    '''
    Creates a generated function alias that initializes decorator class then calls
    the instance and returns any values.

    Doc strings are also copied to wrapper so they are available to salt command
    line interface via the --doc option.
    '''
    def outer(func):
        def wrapper(*varargs, **kwargs):
            module = func(*varargs, **kwargs)
            return module()
        wrapper.func = func
        if 'usage' in dir(func):
            wrapper.__doc__ = func.usage()
        else:
            wrapper.__doc__ = func.__doc__
        wrapper.__name__ = new_name
        frame = stack()[0][0]
        func_globals = frame.f_globals
        func_globals_save = {new_name: wrapper}
        func_globals.update(func_globals_save)
        return func
    return outer


def _get_vm(vmname):
    return _VMAction.get_vm(vmname)


def _run_all(cmd, **options):
    if isinstance(cmd, list):
        cmd = ' '.join(cmd)

    result = __salt__['cmd.run_all'](cmd, runas='user', output_loglevel='quiet', **options)
    result.pop('pid', None)
    return result


class _ArgumentParser(argparse.ArgumentParser):
    '''Custom ArgumentParser to raise Salt Exceptions instead of exiting
       the complete process.
    '''
    def error(self, message):
        """error(message: string)

        Raises a Salt CommandExecutionError.

        If you override this in a subclass, it should not return -- it
        should either exit or raise an exception.
        """
        #self.print_usage(_sys.stderr)
        raise CommandExecutionError('{0}: error: {1}\n'.format(self.prog, message))


class _VMAction(argparse.Action):
    '''Custom action to retreive virtual machine settings object.
    '''
    @staticmethod
    def get_vm(vmname):
        '''
        '''
        qvm_collection = QubesVmCollection()
        qvm_collection.lock_db_for_reading()
        qvm_collection.load()
        qvm_collection.unlock_db()
        vm = qvm_collection.get_vm_by_name(vmname)
        if not vm or vm.qid not in qvm_collection:
            return None
        return vm

    def __call__(self, parser, namespace, values, options_string=None):
        '''
        '''
        if not values:
            return None

        vm = self.get_vm(values)
        #if not vm:
        #    raise SaltInvocationError('Error! No VM found with the name of: {0}'.format(values))

        setattr(namespace, self.dest, values)
        setattr(namespace, 'vm', vm)


class _ModuleHelper(object):
    '''Module Helper is meant to be sub-classed and contains code pieces that
       would otherwise be duplicated.
    '''
    def __init__(self, arginfo, *varargs, **kwargs):
        self.arginfo = arginfo
        self.ret = {'result': None,
                    'retcode': 0,
                    'stdout': '',
                    'stderr': '',
                    'changes': {},
                    }
        self.stdout = ''
        self.stderr = ''
        #self.cmd = ''
        self.post_run_hook = None

    @classmethod
    def _parser(cls):
        '''Argparse definitions.

        Implement in sub-class.
        '''
        return None

    @classmethod
    def usage(cls):
        '''Help docs and usage info for when salt-call -doc module.func called.
        '''
        parser = cls._parser()
        if not parser:
            return cls.__doc__
        else:
            usage_header = '=== USAGE ' + '='*70 + '\n'
            doc_header = '=== DOCS ' + '='*71 + '\n'
            return '{0}{1}\n{2}{3}'.format(doc_header, cls.__doc__, usage_header, parser.format_help())

    def update(self, result, create=True, append=[]):
        '''Updates object infomation from passed result.
        '''
        _update(self.ret, result, create=create, append=append)

    def run(self, cmd, ignore_test=False, post_hook=None, **options):
        '''Executes cmd using salt.utils run_all function.

        Fake results are returned instead of executing the command if test
        mode is enabled.
        '''
        # XXX: Reset result in case of multiple calls to run
        self.ret['result'] = None

        cmd_string = 'cmd: {0}'.format(cmd)
        if options:
            cmd_string += ' options: {0}'.format(options)

        #linefeed = '\n' if self.cmd else ''
        #self.cmd += linefeed + cmd_string

        if __opts__['test'] and not ignore_test:
            # XXX: TODO: Remove any TEST code from here; add to sub-class
            #      test() and maybe have sub-class call this super()
            self.test()
            result = self.ret
        else:
            result = _run_all(cmd, **options)

            # Post-run hooks
            self.run_post(cmd, result)
            if post_hook:
                post_hook(cmd, result)
            if self.post_run_hook:
                self.post_run_hook(cmd, result)

            if result['retcode']:
                self.ret['retcode'] = result['retcode']

        linefeed = '\n' if self.stdout else ''
        if __opts__['test']:
            status = 'failed' if result['retcode'] else 'passed'
            self.stdout += 'Test {0}: {1}'.format(status, cmd_string)
        else:
            self.stdout += linefeed + cmd_string

        linefeed = '\n' if self.stdout else ''
        if result['stdout']:
            self.stdout += linefeed + result['stdout']

        linefeed = '\n' if self.stderr and result['stderr'] else ''
        self.stderr += linefeed + result['stderr']

        result.setdefault('changes', {})
        return result

    def run_post(self, cmd, result):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc

        Implement in sub-class.
        '''
        return None

    def test(self):
        '''Called by run if test mode enabled.

        Implement in sub-class.
        '''
        return None

    def vm(self, fail=True):
        '''Returns VM object if it exists.

        Will raise a SaltInvocationError if fail=True and no VM exists
        '''
        if hasattr(self, 'args') and hasattr(self.args, 'vm'):
            if self.args.vm:
                return self.args.vm
        if fail:
            raise SaltInvocationError(message='Virtual Machine does not exist!')
        else:
            return None

    def results(self, msg_all='', msg_passed='', msg_failed=''):
        '''Returns the 'ret' (results) dictionary.

        Additional messages may be appended to stdout

        msg_all:
            Append message for passed and failed result

        msg_passed:
            Only append message if result passed

        msg_failed:
            Only append message if result failed
        '''

        self.ret.setdefault('stdout', '')
        self.ret.setdefault('stderr', '')

        linefeed = '\n' if self.stdout else ''
        if msg_all:
            self.stdout += linefeed + msg_all
        elif msg_passed:
            self.stdout += linefeed + msg_passed
        elif msg_failed:
            self.stdout += linefeed + msg_failed

        linefeed = '\n' if self.stdout and self.ret['stdout'] else ''
        self.ret['stdout'] += linefeed + self.stdout

        linefeed = '\n' if self.stderr and self.ret['stderr'] else ''
        self.ret['stderr'] += linefeed + self.stderr

        return self.ret


@_function_alias('check')
class _Check(_ModuleHelper):
    '''
    Check if a virtual machine exists::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.check <vmname> exists flags=[quiet]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Positional
        - check:                (exists)|absent

        # Optional Flags
        - flags:
          - quiet
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        self.post_run_hook = kwargs.pop('post-run-hook', None)

        super(_Check, self).__init__(arginfo(['flags'], skip=['varargs']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        # Remove 'check' variable from varargs since qvm-check does not support it
        try:
            self.arginfo['__argv'].remove(self.args.check)
        except ValueError:
            pass

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.check')

        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('check', nargs='?', default='exists', choices=('exists', 'absent'), help='Check if virtual machine exists or not')
        return parser

    def run_post(self, cmd, result):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc
        '''
        if self.args.check.lower() == 'absent':
            result['retcode'] = not result['retcode']

    def __call__(self):
        args = self.args

        #def post_hook(cmd, result):
        #    if self.args.check.lower() == 'absent':
        #        result['retcode'] = not result['retcode']
        #    if self.post_run_hook:
        #        self.post_run_hook(cmd, result)

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-check {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd, ignore_test=True)
        #result = self.run(cmd, ignore_test=True, post_hook=post_hook)

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('state')
class _State(_ModuleHelper):
    '''
    Return virtual machine state::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.state <vmname> running

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Positional
        - state:                (status)|running|dead|transient|paused
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        argv_ordering = ['args', 'varargs', 'argparse_keywords']
        super(_State, self).__init__(arginfo(argv_ordering=argv_ordering, skip=['varargs']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.state')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('state', nargs='?', default='status', choices=('status', 'running', 'dead', 'transient', 'paused'), help='Check power state of virtual machine')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        self.stdout = self.vm().get_power_state()
        power_state = self.stdout.strip().lower()

        if args.state.lower() == 'running':
            if power_state not in ['running']:
                self.ret['retcode'] = 1
        elif args.state.lower() == 'dead':
            if power_state not in ['halted']:
                self.ret['retcode'] = 1
        elif args.state.lower() == 'transient':
            if power_state not in ['transient']:
                self.ret['retcode'] = 1
        elif args.state.lower() == 'paused':
            if power_state not in ['paused']:
                self.ret['retcode'] = 1
        #else:
        #    self.ret['retcode'] = not self.vm().is_guid_running()

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('create')
class _Create(_ModuleHelper):
    '''
    Create a new virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.create <vmname> label=red template=fedora-21 flags=[proxy]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional
        - template:             <template>
        - label:                <label>
        - mem:                  <mem>
        - vcpus:                <vcpus>
        - root-move-from:       <root_move>
        - root-copy-from:       <root_copy>

        # Optional Flags
        - flags:
          - proxy
          - hvm
          - hvm-template
          - net
          - standalone
          - internal
          - force-root
          - quiet
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Create, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.create')

        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--proxy', action='store_true', help='Create ProxyVM')
        parser.add_argument('--hvm', action='store_true', help='Create HVM (standalone unless --template option used)')
        parser.add_argument('--hvm-template', action='store_true', help='Create HVM template')
        parser.add_argument('--net', action='store_true', help='Create NetVM')
        parser.add_argument('--standalone', action='store_true', help='Create standalone VM - independent of template')
        parser.add_argument('--internal', action='store_true', help='Create VM for internal use only (hidden in qubes- manager, no appmenus)')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Optional
        parser.add_argument('--template', nargs=1, help='Specify the TemplateVM to use')
        parser.add_argument('--label', nargs=1, help='Specify the label to use for the new VM (e.g. red, yellow, green, ...)')
        parser.add_argument('--root-move-from', nargs=1, help='Use provided root.img instead of default/empty one (file will be MOVED)')
        parser.add_argument('--root-copy-from', nargs=1, help='Use provided root.img instead of default/empty one (file will be COPIED)')
        parser.add_argument('--mem', nargs=1, help='Initial memory size (in MB)')
        parser.add_argument('--vcpus', nargs=1, help='VCPUs count')

        # Required Positional
        parser.add_argument('vmname', help='Virtual machine name')
        return parser

    def __call__(self):
        args = self.args

        def post_hook(cmd, result):
            if result['retcode']:
                result['result'] = result['retcode']
                result['retcode'] = 0

        # Check if VM exists; always indicate pass
        #current_check_result = check(args.vmname)
        current_check_result = check(args.vmname, **{'post-run-hook': post_hook})

        self.update(current_check_result, create=True, append=['stderr', 'stdout'])
        #if not current_check_result['retcode']:
        #    current_check_result['retcode'] = 0
        #    return current_check_result
        if current_check_result['result']:
            current_check_result['retcode'] = 0
            return current_check_result

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-create {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('remove')
class _Remove(_ModuleHelper):
    '''
    Remove an existing virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.remove <vmname> flags=[just-db]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Flags
        - flags:
          - just-db:
          - force-root
          - quiet
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Remove, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.remove')

        # Optional Flags
        parser.add_argument('--just-db', action='store_true', help='Remove only from the Qubes Xen DB, do not remove any files')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state not in ['halted']:
            result = kill(args.vmname)
            if result['retcode']:
                return result

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-remove {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # Returns the 'ret' dictionary and adds comments in 'test' mode
        return self.results()


@_function_alias('clone')
class _Clone(_ModuleHelper):
    '''
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.clone <vm-name> <target_name> [shutdown=true|false] [path=]

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - target:               <target clone name>

        # Optional
        - path:                 </path/xxx>

        # Optional Flags
        - flags:
          - shutdown
          - force-root
          - quiet
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # XXX: add flags
        argv_ordering = ['keywords', 'args', 'varargs']
        super(_Clone, self).__init__(arginfo(['flags'], argv_ordering=argv_ordering, skip=['varargs']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
        if '--shutdown' in self.arginfo['__argv']:
            self.arginfo['__argv'].remove('--shutdown')

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.clone')

        # Optional Flags
        parser.add_argument('--shutdown', action='store_true', help='Will shutdown a running or paused VM to allow cloning')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Optional
        parser.add_argument('--path', nargs=1, help='Specify path to the template directory')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('target', nargs=1, help='New clone VM name')
        return parser

    def __call__(self):
        args = self.args

        # Check if 'target' VM exists; fail if it does and return
        target_check_result = check(args.target)
        if not target_check_result['retcode']:
            target_check_result['retcode'] = 1
            return target_check_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Command to run: {0}'.format(cmd)
        #    return self.results()

        # Check VM power state and shutdown vm if 'shutdown' is enabled
        if args.shutdown:
            current_state_result = state(args.vmname)
            power_state = current_state_result['stdout'].strip().lower()
            if power_state not in ['halted']:
                shutdown_result = shutdown(args.vmname, *['wait'])
                if shutdown_result['retcode']:
                    return shutdown_result

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-clone {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # Returns the 'ret' dictionary
        return self.results()


def get_prefs(vmname, *vars, **kwargs):
    '''
    Return the current preferences for vmname::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.get_prefs <vm-name>
    '''
    vm = _get_vm(vmname)
    if not vm:
        return {}

    ret = {}
    args, prefs = salt.utils.arg_lookup(__salt__['qvm.prefs']).values()
    for key in prefs:
        value = getattr(vm, key, None)
        value = getattr(value, 'name', value)
        ret[key] = value
    return ret


#def prefs(vmname,
#          include_in_backups=MARKER,
#          pcidevs=MARKER,
#          label=MARKER,
#          netvm=MARKER,
#          maxmem=MARKER,
#          memory=MARKER,
#          kernel=MARKER,
#          template=MARKER,
#          vcpus=MARKER,
#          kernelopts=MARKER,
#          name=MARKER,
#          drive=MARKER,
#          mac=MARKER,
#          debug=MARKER,
#          default_user=MARKER,
#          qrexec_installed=MARKER,
#          guiagent_installed=MARKER,
#          seamless_gui_mode=MARKER,
#          qrexec_timeout=MARKER,
#          timezone=MARKER,
#          internal=MARKER,
#          autostart=MARKER):
def prefs(vmname, *varargs, **kwargs):
    '''
    Set preferences for a virtual machine domain

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.set_prefs <vm_name> label=orange

    Calls the qubes utility directly since the currently library really has
    no validation routines whereas the script does.

    .. code-block:: yaml

        - name:                 <vmname>
        - include_in_backups:   true|false
        - pcidevs:              [string,]
        - label:                red|yellow|green|blue|purple|orange|gray|black
        - netvm:                <string>
        - maxmem:               <int>
        - memory:               <int>
        - kernel:               <string>
        - template:             <string>
        - vcpus:                <int>
        - kernelopts:           <string>
        - drive:                <string>
        - mac:                  <string> (auto)
        - debug:                true|(false)
        - default_user:         <string>
        - qrexec_installed:     true|false
        - guiagent_installed:   true|false
        - seamless_gui_mode:    true|false
        - qrexec_timeout:       <int> (60)
        - timezone:             <string>
        - internal:             true|(false)
        - autostart:            true|(false)
        - flags:
          - list
          - set
          - gry
          - force-root


    '''
    # XXX: Convert to argparse
    include_in_backups = kwargs.pop('include_in_backups', MARKER)
    pcidevs = kwargs.pop('pcidevs', MARKER)
    label = kwargs.pop('label', MARKER)
    netvm = kwargs.pop('netvm', MARKER)
    maxmem = kwargs.pop('maxmem', MARKER)
    memory = kwargs.pop('memory', MARKER)
    kernel = kwargs.pop('kernel', MARKER)
    template = kwargs.pop('template', MARKER)
    vcpus = kwargs.pop('vcpus', MARKER)
    kernelopts = kwargs.pop('kernelopts', MARKER)
    name = kwargs.pop('name', MARKER)
    drive = kwargs.pop('drive', MARKER)
    mac = kwargs.pop('mac', MARKER)
    debug = kwargs.pop('debug', MARKER)
    default_user = kwargs.pop('default_user', MARKER)
    qrexec_installed = kwargs.pop('qrexec_installed', MARKER)
    guiagent_installed = kwargs.pop('guiagent_installed', MARKER)
    seamless_gui_mode = kwargs.pop('seamless_gui_mode', MARKER)
    qrexec_timeout = kwargs.pop('qrexec_timeout', MARKER)
    timezone = kwargs.pop('timezone', MARKER)
    internal = kwargs.pop('internal', MARKER)
    autostart = kwargs.pop('autostart', MARKER)

    ret = {'retcode': 0, 'changes': {}, 'cmd': ''}
    stdout = stderr = ''

    # Get only values passed to function and not the same as in current_state
    current_state =  get_prefs(vmname)
    data = dict([(key, value) for key, value in locals().items() if key in current_state and value != MARKER])

    if not data:
        return current_state
    else:
        data = dict([(key, value) for key, value in data.items() if value != current_state[key]])

    if data:
        for key, value in data.items():
            cmd = "/usr/bin/qvm-prefs {0} -s {1} {2}".format(vmname, key, value)
            result = __salt__['cmd.run_all'](cmd, runas='user')
            ret['cmd'] += 'cmd: {0}\n'.format(cmd)

            if result['retcode']:
                ret['retcode'] = result['retcode']
                if 'stderr' in result and result['stderr'].strip():
                    stderr += '{0}: {1}\n{2}'.format(key, value, result['stderr'])
            else:
                ret['changes'][key] = {}
                ret['changes'][key]['old'] = current_state[key]
                ret['changes'][key]['new'] = value
                if 'stdout' in result and result['stdout'].strip():
                    stdout += result['stdout'] + '\n'
    else:
        stdout = 'Preferences for {0} are already in desired state!'.format(vmname)

    if stderr:
        ret['stdout'] = stderr
    else:
        ret['stdout'] = stdout
    return ret


@_function_alias('service')
class _Service(_ModuleHelper):
    '''
    Manage a virtual machine domain services::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.service <vm-name> [action] [service-name]

    Valid actions: list, enable, disable, default

    .. code-block:: yaml

        - name:                 <vmname>
        - enable:               [string,]
        - disable:              [string,]
        - default:              [string,]
        - list:                 [string,]
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''Only varargs are processed.

        arginfo is also not needed for argparse.
        '''
        # XXX: add flags
        argv_ordering = ['args', 'varargs']
        super(_Service, self).__init__(arginfo(argv_ordering=argv_ordering, skip=['varargs']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.service')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('action', nargs='?', default='list', choices=('list', 'enable', 'disable', 'default'), help='Action to take on service')
        parser.add_argument('service_names', nargs='*', default=[], help='List of Service names to reset')
        return parser

    def __call__(self):
        args = self.args
        current_services = self.vm().services

        # Return all current services if a 'list' only was selected
        if args.action in ['list']:
            return current_services

        for service_name in args.service_names:
            # Execute command (will not execute in test mode)
            cmd = '/usr/bin/qvm-service {0} --{1} {2}'.format(args.vmname, args.action, service_name)
            result = self.run(cmd)

            if not result['retcode']:
                # Attempt to predict result in test mode
                if __opts__['test']:
                    updated_services = copy.deepcopy(current_services)
                    result['stdout'] = ''
                    result['stderr'] = ''

                    if args.action in ['enable', 'disable']:
                        updated_services[service_name] = True
                    elif args.action in ['default']:
                        updated_services.pop(service_name, None)
                else:
                    updated_services = service(args.vmname)

                # Changes
                differ = DictDiffer(current_services, updated_services)
                if differ.changed():
                    self.ret['changes'].setdefault(service_name, {})
                    self.ret['changes'][service_name]['old'] = current_services.get(service_name, None)
                    self.ret['changes'][service_name]['new'] = updated_services[service_name]
                    if 'stdout' in result and result['stdout'].strip():
                        self.stdout += result['stdout'] + '\n'
                else:
                    self.stdout += '{0} "{1}": Service is already in desired state: {2}\n'.format(args.action, service_name, updated_services.get(service_name, 'missing'))

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('run')
class _Run(_ModuleHelper):
    '''
    Run an application within a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.run [options] <vm-name> [<cmd>]

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>
        - user:                 <user>
        - exclude:              <exclude_list>
        - localcmd:             <localcmd>
        - color-output:         <color_output>
        - flags:
          - quiet
          - auto
          - tray
          - all
          - pause
          - unpause
          - pass-io
          - nogui
          - filter-escape-chars
          - no-filter-escape-chars
          - no-color-output
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # Seperate out 'cmd'
        #cmd = self.cmd = kwargs.pop('cmd', '')
        #self.cmd = kwargs.pop('cmd', '')
        cmd = kwargs.pop('cmd', '')

        # XXX if we are successful using args and kwargs; will not need flags?
        # XXX Test using argv_ordering
        # XXX: add flags
        argv_ordering = ['varargs', 'keywords', 'args', 'cmd']
        super(_Run, self).__init__(arginfo(['flags'], argv_ordering=argv_ordering))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        # vmname should go near last
        #self.arginfo['__argv'].remove(vmname)
        #self.arginfo['__argv'].append(vmname)

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.run')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--auto', action='store_true', help='Auto start the VM if not running')
        parser.add_argument('--tray', action='store_true', help='Use tray notifications instead of stdout')
        parser.add_argument('--all', action='store_true', help='Run command on all currently running VMs (or all paused, in case of --unpause)')
        parser.add_argument('--pause', action='store_true', help="Do 'xl pause' for the VM(s) (can be combined this with --all)")
        parser.add_argument('--unpause', action='store_true', help="Do 'xl unpause' for the VM(s) (can be combined this with --all)")
        parser.add_argument('--pass-io', action='store_true', help='Pass stdin/stdout/stderr from remote program (implies -q)')
        parser.add_argument('--nogui', action='store_true', help='Run command without gui')
        parser.add_argument('--filter-escape-chars', action='store_true', help='Filter terminal escape sequences (default if output is terminal)')
        parser.add_argument('--no-filter-escape-chars', action='store_true', help='Do not filter terminal escape sequences - overrides --filter-escape-chars, DANGEROUS when output is terminal')
        parser.add_argument('--no-color-output', action='store_true', help='Disable marking VM output with red color')

        parser.add_argument('--user', nargs=1, help='Run command in a VM as a specified user')
        parser.add_argument('--localcmd', nargs=1, help='With --pass-io, pass stdin/stdout/stderr to the given program')
        parser.add_argument('--color-output', nargs=1, help='Force marking VM output with given ANSI style (use 31 for red)')
        parser.add_argument('--exclude', default=list, nargs='*', help='When --all is used: exclude this VM name (may be repeated)')

        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('cmd', nargs='*', help='Command to run')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state and start if 'auto' is enabled
        if args.auto:
            current_state_result = state(args.vmname)
            power_state = current_state_result['stdout'].strip().lower()
            if power_state not in ['running']:
                start_result = start(args.vmname, *['quiet', 'no-guid'])
                if start_result['retcode']:
                    return start_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Command to run: {0}'.format(cmd)
        #    return self.results()

        # Execute command (will not execute in test mode)
        # XXX: Test using new argv_ordering
        #cmd = '/usr/bin/qvm-run {0} {1} {2}'.format(' '.join(self.arginfo['__argv']), args.vmname, self.cmd)
        cmd = '/usr/bin/qvm-run {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('start')
class _Start(_ModuleHelper):
    '''
    Start a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.start <vm-name>

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>
        - drive:                <drive>
        - hddisk:               <drive_hd>
        - cdrom:                <drive_cdrom>
        - custom-config:        <custom_config>
        - flags:
          - quiet
          - tray
          - no-guid
          - dvm
          - debug
          - install-windows-tools
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # Tell arginfo to also add flags values to argv; will remove flags
        # from argv, only converting the values
        super(_Start, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        # vmname should go last
        #self.arginfo['__argv'].remove(vmname)
        #self.arginfo['__argv'].append(vmname)

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.start')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--tray', action='store_true', help='Use tray notifications instead of stdout')
        parser.add_argument('--no-guid', action='store_true', help='Do not start the GUId (ignored)')
        parser.add_argument('--install-windows-tools', action='store_true', help='Attach Windows tools CDROM to the VM')
        parser.add_argument('--dvm', action='store_true', help='Do actions necessary when preparing DVM image')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode for this VM (until its shutdown)')
        parser.add_argument('--drive', help="Temporarily attach specified drive as CD/DVD or hard disk (can be specified with prefix 'hd:' or 'cdrom:', default is cdrom)")
        parser.add_argument('--hddisk', help='Temporarily attach specified drive as hard disk')
        parser.add_argument('--cdrom', help='Temporarily attach specified drive as CD/DVD')
        parser.add_argument('--custom-config', help='Use custom Xen config instead of Qubes-generated one')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state in ['paused']:
            self.vm().unpause()
        elif power_state not in ['halted']:
            current_state_result['retcode'] = 0 if power_state in ['running', 'transient'] else 1
            return current_state_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Virtual Machine will be started'
        #    return self.results()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-start {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # XXX: Temp hack to prevent startup status showing as Transient
        try:
            if not self.vm().is_guid_running():
                self.vm().start_guid()
        except AttributeError:
            # AttributeError: CEncodingAwareStringIO instance has no attribute 'fileno'
            pass

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('shutdown')
class _Shutdown(_ModuleHelper):
    '''
    Shutdown a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.shutdown <vm-name>

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>
        - exclude:              [exclude_list]
        - flags:
          - quiet
          - force
          - wait
          - all
          - kill
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # Tell arginfo to also add flags values to argv; will remove flags
        # from argv, only converting the values
        super(_Shutdown, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        # vmname should go last
        #self.arginfo['__argv'].remove(vmname)
        #self.arginfo['__argv'].append(vmname)

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.shutdown')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('--quiet', action='store_true', default=False, help='Quiet')
        parser.add_argument('--kill', action='store_true', default=False, help='Kill VM')
        parser.add_argument('--force', action='store_true', help='Force operation, even if may damage other VMs (eg shutdown of NetVM)')
        parser.add_argument('--wait', action='store_true', help='Wait for the VM(s) to shutdown')
        parser.add_argument('--all', action='store_true', help='Shutdown all running VMs')
        parser.add_argument('--exclude', action='store', default=[], nargs='*',
                            help='When --all is used: exclude this VM name (may be repeated)')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state in ['halted']:
            current_state_result['retcode'] = 0
            return current_state_result
        elif power_state in ['paused']:
            self.vm().unpause()

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Virtual Machine will be shutdown'
        #    return self.results()

        # Execute command (will not execute in test mode)
        if self.args.kill:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
        else:
            cmd = '/usr/bin/qvm-shutdown {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

        # Kill if 'Transient'
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state not in ['halted']:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
            result = self.run(cmd)

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('kill')
class _Kill(_ModuleHelper):
    '''
    Kills a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.kill <vmname>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Kill, self).__init__(arginfo())
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.kill')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        return parser

    def __call__(self):
        args = self.args
        self.arginfo['varargs'].append('kill')

        # Set self.ret since 'shutdown' module was called and not run()
        self.ret = shutdown(args.vmname, *self.arginfo['varargs'], **self.arginfo['kwargs'])

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('pause')
class _Pause(_ModuleHelper):
    '''
    Pause a virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.pause <vm-name>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # Tell arginfo to also add flags values to argv; will remove flags
        # from argv, only converting the values
        super(_Pause, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.pause')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state not in ['paused', 'running', 'transient']:
            current_state_result['retcode'] = 1
            return current_state_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Virtual Machine will be paused'
        #    return self.results()

        # Execute command (will not execute in test mode)
        self.vm().pause()

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('unpause')
class _Unpause(_ModuleHelper):
    '''
    Unpause a virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.unpause <vm-name>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        # Tell arginfo to also add flags values to argv; will remove flags
        # from argv, only converting the values
        super(_Unpause, self).__init__(arginfo(['flags']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.unpause')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        return parser

    def __call__(self):
        args = self.args

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state not in ['paused']:
            current_state_result['retcode'] = 0 if power_state in ['running'] else 1
            return current_state_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.stdout = 'Virtual Machine will be unpaused'
        #    return self.results()

        # Execute command (will not execute in test mode)
        self.vm().unpause()

        # Returns the 'ret' dictionary
        return self.results()
