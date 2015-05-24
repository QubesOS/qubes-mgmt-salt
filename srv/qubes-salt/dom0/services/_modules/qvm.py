# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

============================
Qubes qvm-* modules for salt
============================

    SaltInvocationError
        raise when criteria is not met

    CommandExecutionError
        raise when error executing command
'''

# Import python libs
import os
import subprocess
import copy
import inspect
import argparse
import logging

from inspect import getargvalues, stack

# Salt libs
import salt.utils
from salt.utils import which as _which
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Other salt related utilities
from differ import DictDiffer, ListDiffer
from qubes_utils import tostring as _tostring
from qubes_utils import tolist as _tolist
from qubes_utils import arg_info as _arg_info
from qubes_utils import get_fnargs as _get_fnargs
from qubes_utils import alias as _alias
from qubes_utils import update as _update

# Qubes libs
from qubes.qubes import QubesVmCollection

# Enable logging
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


def _function_alias(new_name):
    '''
    Creates a generated function alias that initializes decorator class then calls
    the instance and returns any values.

    Doc strings are also copied to wrapper so they are available to salt command
    line interface via the --doc option.
    '''
    def outer(func):
        func.__virtualname__ = '{0}.{1}'.format(__virtualname__, new_name)

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


# XXX: Move to utils
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


class _QVMBase(object):
    '''QVMBase is a base class which contains base functionality and utility
       to implement the qvm-* commands
    '''

    # Used to identify values that have not been passed to functions which allows
    # the function modules not to have to know anything about the default types
    # excpected
    try:
        if MARKER:
            pass
    except NameError:
        MARKER = object()


    def __init__(self, vmname, *varargs, **kwargs):
        self.data = self.data_create()
        self.linefeed = '\n\n'

        if not hasattr(self, 'arg_options'):
            self.arg_options = self.arg_options_create()

        # PARSE and validate options
        self.parser = self._parser()
        argv = _arg_info(**self.arg_options)['__argv']
        self.args = self.parser.parse_args(args=argv)

        # ADD skipped values to argparse namespace
        setattr(self.args, 'run_post_hook', kwargs.get('run-post-hook', None))

        # SKIP keywords not intended to be passed on to Qubes apps
        self.arg_options['skip'].append('strict')

        # UPDATE 'arg_info' with current argv options
        self.arg_info = _arg_info(**self.arg_options)

    @classmethod
    def _parser_arguments_default(cls, parser):
        '''Default argparse definitions.
        '''
        parser.add_argument('--run-post-hook', action='store', nargs=1, type=object, help='run command post process hook function')
        parser.add_argument('--strict', action='store_true', help='Strict results will fail if pre-conditions are not met')

    @classmethod
    def _parser(cls):
        '''Argparse Parser.
        '''
        parser = _ArgumentParser(prog=cls.__virtualname__)

        # Add default parser arguments
        cls._parser_arguments_default(parser)

        # Add sub-class parser arguments
        cls.parser_arguments(parser)

        return parser

    @classmethod
    def parser_arguments(cls, parser):
        '''Parser arguments.

        Implement in sub-class.
        '''
        pass

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

    def arg_options_create(self, keyword_flag_keys=None, argv_ordering=None, skip=None):
        '''Default arg_info options.
        '''
        data = {}
        data['keyword_flag_keys'] = keyword_flag_keys or ['flags']
        data['argv_ordering'] = argv_ordering or ['flags', 'keywords', 'args', 'varargs']
        data['skip'] = skip or ['run-post-hook']

        self.arg_options = copy.deepcopy(data)
        return self.arg_options

    def data_create(self, result=None, retcode=0, stdout='', stderr='', changes={}, **kwargs):
        data = dict(result=result, retcode=retcode, stdout=stdout, stderr=stderr, changes=changes)
        data.update(**kwargs)
        return copy.deepcopy(data)

    def data_defaults(self, data):
        data.setdefault('result', None)
        data.setdefault('retcode', 0)
        data.setdefault('stdout', '')
        data.setdefault('stderr', '')
        data.setdefault('changes', {})
        return data

    # Get rid of update; use data_merge
    def update(self, result, create=True, append=[]):
        '''Updates object infomation from passed result.
        '''
        _update(self.data, result, create=create, append=append)

    def data_merge(self, result=None, status=None, message=''):
        '''Merges data from individual results into master data dictionary
        which will be returned and includes all changes and comments as well
        as the overall result status
        '''
        # Create a default result if it does not exist
        if not result:
            result = self.data_create()

        # Make sure all the defaults of result are set
        else:
            self.data_defaults(result)

        # ----------------------------------------------------------------------
        # Merge result['retcode']
        # ----------------------------------------------------------------------
        if result['retcode']:
            self.data['retcode'] = result['retcode']

        # ----------------------------------------------------------------------
        # Merge result['result']
        # ----------------------------------------------------------------------
        # - Allows sub-class to keep track of overall pass/fail instead of having
        #   to track 'retcode' when multiple run calls exist
        # - results() will over-write 'retcode' with 'result' if not None
        if 'result' in result and result['result'] is not None:
            self.data['result'] = result['result']

        # ----------------------------------------------------------------------
        # Merge result['stdout'] + result['stderr']
        # ----------------------------------------------------------------------
        if status is None:
            status = '[FAIL] ' if result['retcode'] else '[PASS] '
        indent = ' ' * len(status)

        if result['retcode'] and result['stderr'].strip():
            linefeed = self.linefeed if self.data['stderr'] else ''
            if message:
                self.data['stderr'] += '{0}{1}{2}'.format(linefeed, status, message)
            if result['stdout'].strip():
                self.data['stderr'] += '\n{0}{1}'.format(indent, result['stdout'].strip().replace('\n', '\n' + indent))
            if result['stderr'].strip():
                self.data['stderr'] += '\n{0}{1}'.format(indent, result['stderr'].strip().replace('\n', '\n' + indent))
        else:
            linefeed = self.linefeed if self.data['stdout'] else ''
            if message:
                self.data['stdout'] += '{0}{1}{2}'.format(linefeed, status, message)
            if result['stdout'].strip():
                self.data['stdout'] += '\n{0}{1}'.format(indent, result['stdout'].strip().replace('\n', '\n' + indent))

        # ----------------------------------------------------------------------
        # Merge result['changes']
        # ----------------------------------------------------------------------
        changes = result.get('changes', None)
        if changes and not result['retcode'] and not __opts__['test']:
            name = self.__virtualname__
            self.data['changes'].setdefault(name, {})
            for key, value in changes.items():
                self.data['changes'][name][key] = value

        return result

    def run(self, cmd, test_ignore=False, post_hook=None, data=None, **options):
        '''Executes cmd using salt.utils run_all function.

        Fake results are returned instead of executing the command if test
        mode is enabled.
        '''
        if __opts__['test'] and not test_ignore:
            self.test()
            result = self.data_create()
        else:
            if isinstance(cmd, list):
                cmd = ' '.join(cmd)

            result = __salt__['cmd.run_all'](cmd, runas='user', output_loglevel='quiet', **options)
            result.pop('pid', None)
            result = self.data_defaults(result)
            #result.setdefault('changes', {})

        self._run_post_hook(post_hook, cmd, result, data)

        cmd_options = str(options) if options else ''
        cmd_string = '{0} {1}'.format(cmd, cmd_options)

        return self.data_merge(result, message=cmd_string)

    def _run_post_hook(self, post_hook, cmd, result, data):
        '''Execute and post hooks if they exist.
        '''
        self.run_post(cmd, result, data)
        if post_hook:
            post_hook(cmd, result, data)
        if self.args.run_post_hook:
            self.args.run_post_hook(cmd, result, data)

    def run_post(self, cmd, result, data):
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
        '''Returns the results 'data' (results) dictionary.

        Additional messages may be appended to stdout

        msg_all:
            Append message for passed and failed result

        msg_passed:
            Only append message if result passed

        msg_failed:
            Only append message if result failed
        '''

        self.data.setdefault('stdout', '')
        self.data.setdefault('stderr', '')

        linefeed = '\n' if self.data['stdout'] else ''
        if msg_all:
            self.data['stdout'] += linefeed + msg_all
        elif msg_passed:
            self.data['stdout'] += linefeed + msg_passed
        elif msg_failed:
            self.data['stdout'] += linefeed + msg_failed

        # Use 'result' over 'retcode' if result is not None as 'retcode'
        # reflects last run state, where 'result' is set explicitly
        if self.data['result'] is not None:
            self.data['retcode'] = self.data['result']

        return self.data


@_function_alias('check')
class _Check(_QVMBase):
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
        self.arg_options_create()['skip'].append('varargs')
        super(_Check, self).__init__(vmname, *varargs, **kwargs)

        # Remove 'check' variable from varargs since qvm-check does not support it
        try:
            self.arg_info['__argv'].remove(self.args.check)
        except ValueError:
            pass

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('check', nargs='?', default='exists', choices=('exists', 'absent'), help='Check if virtual machine exists or not')

    def run_post(self, cmd, result, data):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc
        '''
        if self.args.check.lower() == 'absent':
            result['retcode'] = not result['retcode']

    def __call__(self):
        args = self.args

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-check {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd, test_ignore=True)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('state')
class _State(_QVMBase):
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
        self.arg_options_create()['skip'].append('varargs')
        super(_State, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # Optional Positional
        parser.add_argument('state', nargs='?', default='status', choices=('status', 'running', 'dead', 'transient', 'paused'), help='Check power state of virtual machine')

    def __call__(self):
        args = self.args

        # Check VM power state
        self.data['stdout'] = self.vm().get_power_state()
        power_state = self.data['stdout'].strip().lower()

        if args.state.lower() == 'running':
            if power_state not in ['running']:
                self.data['retcode'] = 1
        elif args.state.lower() == 'dead':
            if power_state not in ['halted']:
                self.data['retcode'] = 1
        elif args.state.lower() == 'transient':
            if power_state not in ['transient']:
                self.data['retcode'] = 1
        elif args.state.lower() == 'paused':
            if power_state not in ['paused']:
                self.data['retcode'] = 1
        #else:
        #    self.data['retcode'] = not self.vm().is_guid_running()

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('create')
class _Create(_QVMBase):
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
        super(_Create, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
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

    def __call__(self):
        args = self.args

        def absent_post_hook(cmd, result, data):
            if result['retcode']:
                result['result'] = result['retcode']

        absent_result = check(args.vmname, *['absent'], **{'run-post-hook': absent_post_hook})

        # Update locals results
        self.update(absent_result, create=True, append=['stderr', 'stdout'])

        # Return if VM is not absent
        if absent_result['result']:
            # FAIL only in strict mode
            if not args.strict:
                absent_result['retcode'] = 0
            return absent_result

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-create {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('remove')
class _Remove(_QVMBase):
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
        super(_Remove, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--just-db', action='store_true', help='Remove only from the Qubes Xen DB, do not remove any files')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

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
        cmd = '/usr/bin/qvm-remove {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Returns the results 'data' dictionary and adds comments in 'test' mode
        return self.results()


@_function_alias('clone')
class _Clone(_QVMBase):
    '''
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.clone <vm-name> <target_name> [shutdown=true|false] [path=]

    Valid actions:

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
        self.arg_options_create()['skip'].append('varargs')
        super(_Clone, self).__init__(vmname, *varargs, **kwargs)

        # XXX: May be able to just pop this before super call? NO, then not in argparse for validation
        # -- or -- maybe pop now; then re-run arg_info again!
        # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
        if '--shutdown' in self.arg_info['__argv']:
            self.arg_info['__argv'].remove('--shutdown')

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--shutdown', action='store_true', help='Will shutdown a running or paused VM to allow cloning')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Optional
        parser.add_argument('--path', nargs=1, help='Specify path to the template directory')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('target', nargs=1, help='New clone VM name')

    def __call__(self):
        args = self.args

        # Check if 'target' VM exists; fail if it does and return
        target_check_result = check(args.target)
        if not target_check_result['retcode']:
            target_check_result['retcode'] = 1
            return target_check_result

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.data['stdout'] = 'Command to run: {0}'.format(cmd)
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
        cmd = '/usr/bin/qvm-clone {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('prefs')
class _Prefs(_QVMBase):
    '''
    Set preferences for a virtual machine domain

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.prefs <vm_name> label=orange

    Calls the qubes utility directly since the currently library really has
    no validation routines whereas the script does.

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               (list)|set|get|gry

        # Exclusive Positional
        - autostart:            true|(false)
        - debug:                true|(false)
        - default-user:         <string>
        - include-in-backups:   true|false
        - internal:             true|(false)
        - kernel:               <string>
        - kernelopts:           <string>
        - label:                red|yellow|green|blue|purple|orange|gray|black
        - mac:                  <string> (auto)
        - maxmem:               <int>
        - memory:               <int>
        - netvm:                <string>
        - pcidevs:              [string,]
        - template:             <string>
        - qrexec-timeout:       <int> (60)
        - vcpus:                <int>

        # Optional Flags
        - flags:
          - force-root
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        self.arg_options_create(argv_ordering=['flags', 'args', 'action', 'varargs', 'keywords'])['skip'].append('action')
        super(_Prefs, self).__init__(vmname, *varargs, **kwargs)
        print

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        #parser.add_argument('--list', action='store_true')
        #parser.add_argument('--set', action='store_true')
        #parser.add_argument('--gry', action='store_true')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('action', nargs='?', default='list', choices=('list', 'get', 'gry', 'set'))

        # Exclusive Positional
        # Optional
        parser.add_argument('--autostart', nargs='?', type=bool, default=False)
        parser.add_argument('--debug', nargs='?', type=bool, default=False)
        parser.add_argument('--default-user', nargs='?')
        parser.add_argument('--label', nargs='?', choices=('red', 'yellow', 'green', 'blue', 'purple', 'orange', 'gray', 'black'))
        parser.add_argument('--include-in-backups', nargs='?', type=bool)
        parser.add_argument('--internal', nargs='?', type=bool, default=False)
        parser.add_argument('--kernel', nargs='?')
        parser.add_argument('--kernelopts', nargs='?')
        parser.add_argument('--mac', nargs='?')
        parser.add_argument('--maxmem', nargs='?', type=int)
        parser.add_argument('--memory', nargs='?', type=int)
        parser.add_argument('--netvm', nargs='?')
        parser.add_argument('--pcidevs', nargs='*', default=[])
        parser.add_argument('--template', nargs='?')
        parser.add_argument('--qrexec-timeout', nargs='?', type=int, default=60)
        parser.add_argument('--vcpus', nargs='?', type=int)

        ## The following args seem not to exist in the Qubes R3.0 DB
        # drive:                <string>
        # qrexec-installed:     true|false
        # guiagent-installed:   true|false
        # seamless-gui-mode:    true|false
        # timezone:             <string>
        ##parser.add_argument('--timezone', nargs='?')
        ##parser.add_argument('--drive', nargs='?')
        ##parser.add_argument('--qrexec-installed', nargs='?', type=bool)
        ##parser.add_argument('--guiagent-installed', nargs='?', type=bool)
        ##parser.add_argument('--seamless-gui-mode', nargs='?', type=bool)

    def run_post(self, cmd, result, data):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc
        '''
        if not result['retcode']:
            result['changes'].setdefault(data['key'], {})
            result['changes'][data['key']]['old'] = data['value_old']
            result['changes'][data['key']]['new'] = data['value_new']

    def __call__(self):
        args = self.args
        vm = self.vm()

        # Only use single linefeeds for results
        self.linefeed = '\n'

        # ======================================================================
        # XXX: TODO: Implement 'list' and 'get/gry'
        #
        # runpy, execfile
        #
        if args.action in ['list', 'get', 'gry']:
            if args.action in ['list']:
                import os
                import sys
                _locals = dict()
                _globals = dict()
                try:
                    execfile('/usr/bin/qvm-prefs', _globals,_locals)
                except NameError:
                    pass
                properties = _locals.get('properties', []).keys()
            else:
                properties = self.arg_info['kwargs'].keys()

            for key in properties:
                current_value = getattr(vm, key, self.MARKER)
                current_value = getattr(current_value, 'name', current_value)

                if current_value == self.MARKER:
                    continue

                label_width = 19
                fmt="{{0:<{0}}}: {{1}}".format(label_width)

                self.data_merge(status='', message=fmt.format(key, current_value))
                continue

        # ======================================================================
        else:
            for key, value in self.arg_info['kwargs'].items():
                # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
                key = key.replace('-', '_')

                current_value = getattr(vm, key, self.MARKER)
                current_value = getattr(current_value, 'name', current_value)

                # Key does not exist in vm database
                if current_value == self.MARKER:
                    message = '{0} does not exist in VM database!'.format(key)
                    result = self.data_create(retcode=1)
                    self.data_merge(result, message=message)
                    continue

                # Value matches; no need to update
                if value == current_value:
                    message = '{0} is already in desired state: {1}'.format(key, value)
                    self.data_merge(message=message, status='[SKIP] ')
                    continue

                # Execute command (will not execute in test mode)
                data = dict(key=key, value_old=current_value, value_new=value)
                cmd = '/usr/bin/qvm-prefs {0} --set {1} {2} "{3}"'.format(' '.join(self.arg_info['_argparse_flags']), args.vmname, key, value)
                result = self.run(cmd, data=data)

        #if not data:
        #    return current_state
        #else:
        #    data = dict([(key, value) for key, value in data.items() if value != current_state[key]])

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('service')
class _Service(_QVMBase):
    '''
    Manage a virtual machine domain services::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.service <vm-name> [action] [service-name]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - action:               [list|enable|disable|default]
        - service_names:        [string,]
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''Only varargs are processed.

        arg_info is also not needed for argparse.
        '''
        self.arg_options_create(argv_ordering=['args', 'varargs'])['skip'].append('varargs')
        super(_Service, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('action', nargs='?', default='list', choices=('list', 'enable', 'disable', 'default'), help='Action to take on service')
        parser.add_argument('service_names', nargs='*', default=[], help='List of Service names to reset')

    def run_post(self, cmd, result, data):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc
        '''
        #if not result['retcode']:
        #    result['changes'].setdefault(data['key'], {})
        #    result['changes'][data['key']]['old'] = data['value_old']
        #    result['changes'][data['key']]['new'] = data['value_new']
        pass

    def __call__(self):
        args = self.args
        current_services = self.vm().services

        # Only use single linefeeds for results
        self.linefeed = '\n'

        # Return all current services if a 'list' only was selected
        if args.action in ['list']:
            return current_services

        for service_name in args.service_names:
            # Execute command (will not execute in test mode)
            #data = dict(key=key, value_old=current_value, value_new=value)
            cmd = '/usr/bin/qvm-service {0} --{1} {2}'.format(args.vmname, args.action, service_name)
            result = self.run(cmd, data={})

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
                    self.data['changes'].setdefault(service_name, {})
                    self.data['changes'][service_name]['old'] = current_services.get(service_name, None)
                    self.data['changes'][service_name]['new'] = updated_services[service_name]
                    if 'stdout' in result and result['stdout'].strip():
                        self.data['stdout'] += result['stdout']
                else:
                    self.data['stdout'] += '{0} "{1}": Service is already in desired state: {2}'.format(args.action, service_name, updated_services.get(service_name, 'missing'))

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('run')
class _Run(_QVMBase):
    '''
    Run an application within a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.run [options] <vm-name> [<cmd>]

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
        - cmd:                  <run command>

        # Optional
        - user:                 <user>
        - exclude:              <exclude_list>
        - localcmd:             <localcmd>
        - color-output:         <color_output>

        # Optional Flags
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
        self.arg_options_create(argv_ordering=['flags', 'keywords', 'args', 'varargs', 'cmd'])
        super(_Run, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
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

        # Optional
        parser.add_argument('--user', nargs=1, help='Run command in a VM as a specified user')
        parser.add_argument('--localcmd', nargs=1, help='With --pass-io, pass stdin/stdout/stderr to the given program')
        parser.add_argument('--color-output', nargs=1, help='Force marking VM output with given ANSI style (use 31 for red)')
        parser.add_argument('--exclude', default=list, nargs='*', help='When --all is used: exclude this VM name (may be repeated)')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('cmd', nargs='*', default=list, type=list, help='Command to run')

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

        # XXX: TEST; maybe create a loop; or timer...
        current_state_running = state(args.vmname, *['running'])
        if current_state_running['retcode']:
            return current_state_running

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-run {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('start')
class _Start(_QVMBase):
    '''
    Start a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.start <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional
        - drive:                <drive>
        - hddisk:               <drive_hd>
        - cdrom:                <drive_cdrom>
        - custom-config:        <custom_config>

        # Optional Flags
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
        super(_Start, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--tray', action='store_true', help='Use tray notifications instead of stdout')
        parser.add_argument('--no-guid', action='store_true', help='Do not start the GUId (ignored)')
        parser.add_argument('--install-windows-tools', action='store_true', help='Attach Windows tools CDROM to the VM')
        parser.add_argument('--dvm', action='store_true', help='Do actions necessary when preparing DVM image')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode for this VM (until its shutdown)')

        # Optional
        parser.add_argument('--drive', help="Temporarily attach specified drive as CD/DVD or hard disk (can be specified with prefix 'hd:' or 'cdrom:', default is cdrom)")
        parser.add_argument('--hddisk', help='Temporarily attach specified drive as hard disk')
        parser.add_argument('--cdrom', help='Temporarily attach specified drive as CD/DVD')
        parser.add_argument('--custom-config', help='Use custom Xen config instead of Qubes-generated one')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

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

        # XXX: TODO:
        # Got this failure to start... need to make sure messages are verbose, so
        # try testing in this state again once we get around to testing this function
        # if ret == -1: raise libvirtError ('virDomainCreateWithFlags() failed', dom=self)
        # libvirt.libvirtError: Requested operation is not valid: PCI device 0000:04:00.0 is in use by driver xenlight, domain salt-testvm4

        # Attempt to predict result in test mode
        #if __opts__['test']:
        #    self.data['stdout'] = 'Virtual Machine will be started'
        #    return self.results()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-start {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # XXX: Temp hack to prevent startup status showing as Transient
        try:
            if not self.vm().is_guid_running():
                self.vm().start_guid()
        except AttributeError:
            # AttributeError: CEncodingAwareStringIO instance has no attribute 'fileno'
            pass

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('shutdown')
class _Shutdown(_QVMBase):
    '''
    Shutdown a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.shutdown <vm-name>

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>

        # Optional
        - exclude:              [exclude_list]

        # Optional Flags
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
        super(_Shutdown, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--quiet', action='store_true', default=False, help='Quiet')
        parser.add_argument('--kill', action='store_true', default=False, help='Kill VM')
        parser.add_argument('--force', action='store_true', help='Force operation, even if may damage other VMs (eg shutdown of NetVM)')
        parser.add_argument('--wait', action='store_true', help='Wait for the VM(s) to shutdown')
        parser.add_argument('--all', action='store_true', help='Shutdown all running VMs')

        # Optional
        parser.add_argument('--exclude', action='store', default=[], nargs='*',
                            help='When --all is used: exclude this VM name (may be repeated)')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        args = self.args

        # XXX: Should I add back in exists?  Test without it existing as well then...

        # Check VM power state
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state in ['halted']:
            current_state_result['retcode'] = 0
            return current_state_result
        elif power_state in ['paused']:
            self.vm().unpause()

        # ======================================================================
        #def absent_post_hook(cmd, result, data):
        #    if result['retcode']:
        #        result['result'] = result['retcode']

        #absent_result = check(args.vmname, *['absent'], **{'run-post-hook': absent_post_hook})

        ## Update locals results
        #self.update(absent_result, create=True, append=['stderr', 'stdout'])

        ## Return if VM is not absent
        #if absent_result['result']:
        #    # FAIL only in strict mode
        #    if not args.strict:
        #        absent_result['retcode'] = 0
        #    return absent_result
        # ======================================================================

        # Execute command (will not execute in test mode)
        if self.args.kill:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
        else:
            cmd = '/usr/bin/qvm-shutdown {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Kill if 'Transient'
        current_state_result = state(args.vmname)
        power_state = current_state_result['stdout'].strip().lower()
        if power_state not in ['halted']:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
            result = self.run(cmd)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('kill')
class _Kill(_QVMBase):
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
        super(_Kill, self).__init__(vmname, *varargs, **kwargs)
        #self.parser = self.parser_arguments()
        #self.args = self.parser.parse_args(args=self.arg_info['__argv'])

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        args = self.args
        self.arg_info['varargs'].append('kill')

        # Set self.data since 'shutdown' module was called and not run()
        self.data = shutdown(args.vmname, *self.arg_info['varargs'], **self.arg_info['kwargs'])

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('pause')
class _Pause(_QVMBase):
    '''
    Pause a virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.pause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Pause, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

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
        #    self.data['stdout'] = 'Virtual Machine will be paused'
        #    return self.results()

        # Execute command (will not execute in test mode)
        self.vm().pause()

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('unpause')
class _Unpause(_QVMBase):
    '''
    Unpause a virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.unpause <vm-name>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Unpause, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

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
        #    self.data['stdout'] = 'Virtual Machine will be unpaused'
        #    return self.results()

        # Execute command (will not execute in test mode)
        self.vm().unpause()

        # Returns the results 'data' dictionary
        return self.results()
