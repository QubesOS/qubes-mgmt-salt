# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

============================
Qubes qvm-* modules for salt
============================

The following erros are used and raised in the circumstances as indicated:

    SaltInvocationError
        raise when criteria is not met

    CommandExecutionError
        raise when error executing command


-----
TODO:
-----

global:
    Implement a global `debug` mode; and per module to enable debug output

    Move formatting to results module. Considerations for alternative output
    formats

prefs:
    Currently using `execfile` to parse `/usr/bin/qvm-prefs` in order to obtain
    the property list of valid fields that can be set.  Find a better
    alternative solution to retreive the property list.

-----
TESTS
-----
    Check that argparse only allows what intended (some rules may need to be
    created to be excusive)

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

# XXX: TEMP
from stuf import defaultstuf, stuf
from options import Options, OptionsClass, OptionsContext, attrs, Unset

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


class Result(Options):
    def __init__(self, *args, **kwargs):
        defaults = {
            'name':  '',
            'result':  None,
            'retcode': 0,
            'stdout':  '',
            'stderr':  '',
            'data':  None,
            'changes': {},
            'comment': '',
        }

        defaults.update(kwargs)
        super(Result, self).__init__(*args, **defaults)

    def reset(self, key, default=None):
        value = getattr(self, key, default)
        self[key] = type(self[key])()
        return value

    def passed(self, **kwargs):
        return not bool(self.retcode)

    def failed(self, **kwargs):
        return bool(self.retcode)

    def __len__(self):
        return self.passed()


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

    @staticmethod
    def find_key(adict, text):
        for key in adict.keys():
            if key.replace('-', '_') == text:
                return key
        return None

    def __init__(self, vmname, *varargs, **kwargs):
        #internal_options = ['strict', 'result-mode']
        self._data = []
        self._linefeed = '\n'

        if not hasattr(self, 'arg_options'):
            self.arg_options = self.arg_options_create()

        self.parser = self._parser()
        for group in self.parser._action_groups:
            if group.title == 'default':
                for action in group._group_actions:
                    option = self.find_key(kwargs, action.dest) or action.dest.replace('_', '-')
                    self.arg_options['skip'].append(option)

        self.arg_info = _arg_info(**self.arg_options)
        argv = self.arg_info['_argparse_skipped'] + ['--defaults-end'] + self.arg_info['__argv']
        self.args = self.parser.parse_args(args=argv)

        # Type of result mode to use (default: last)
        if 'last' not in self.args.result_mode and 'all' not in self.args.result_mode:
            self.args.result_mode.append('last')

    @classmethod
    def _parser_arguments_default(cls, parser):
        '''Default argparse definitions.
        '''
        parser.add_argument('--result-mode', nargs='*', default=['last'], choices=('last', 'all', 'debug', 'debug-changes'), help='Initial result_mode options')
        parser.add_argument('--run-post-hook', action='store', help='run command post process hook function')
        parser.add_argument('--strict', action='store_true', help='Strict results will fail if pre-conditions are not met')
        parser.add_argument('--defaults-end', action='store_true', default=True, help='Does nothing; signals end of defaults')

    @classmethod
    def _parser(cls):
        '''Argparse Parser.
        '''
        default_parser = _ArgumentParser(add_help=False)

        # Add default parser arguments
        default = default_parser.add_argument_group('default')
        cls._parser_arguments_default(default)

        # Add sub-class parser arguments
        parser = _ArgumentParser(prog=cls.__virtualname__, parents=[default_parser])
        qvm = parser.add_argument_group('qvm')
        cls.parser_arguments(qvm)

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
        data['skip'] = skip or []

        self.arg_options = copy.deepcopy(data)
        return self.arg_options

    def linefeed(self, text):
        return self._linefeed if text else ''

    # XXX: Move formatting functions to Result
    def save_result(self, result=None, retcode=None, data=None, prefix=None, message='', error_message=''):
        '''Merges data from individual results into master data dictionary
        which will be returned and includes all changes and comments as well
        as the overall result status
        '''

        # Create a default result if one does not exist
        if result is None:
            result = Result()
        else:
            # Merge result.retcode
            if retcode is not None:
                result.retcode = retcode

        # Copy args to result. Passed args override result set args
        args = ['data', 'prefix', 'message', 'error_message']
        for arg in args:
            if arg not in result or locals().get(arg, None):
                result[arg] = locals()[arg]

        if not result.name:
            result.name = self.__virtualname__

        if not result.comment:
            # ------------------------------------------------------------------
            # Create comment
            # ------------------------------------------------------------------
            prefix = result.prefix if 'prefix' in result else ''
            message = result.message if 'message' in result else ''
            error_message = result.error_message if 'error_message' in result else ''

            if prefix is None:
                prefix = '[FAIL] ' if result.retcode else '[PASS] '
            indent = ' ' * len(prefix)

            # Manage message
            if result.failed():
                if error_message:
                    message = error_message
            if not message:
                indent = ''

            stdout = stderr = ''
            if result.failed() and result.stderr.strip():
                if message:
                    stderr += '{0}{1}'.format(prefix, message)
                if result.stdout.strip():
                    stderr += '\n{0}{1}'.format(indent, result.stdout.strip().replace('\n', '\n' + indent))
                if result.stderr.strip():
                    stderr += '\n{0}{1}'.format(indent, result.stderr.strip().replace('\n', '\n' + indent))
            else:
                if message:
                    stdout += '{0}{1}'.format(prefix, message)
                if result.stdout.strip():
                    stdout += '\n{0}{1}'.format(indent, result.stdout.strip().replace('\n', '\n' + indent))

            if stderr:
                if stdout:
                    stdout = '====== stdout ======\n{0}\n\n'.format(stdout)
                stderr = '====== stderr ======\n{0}'.format(stderr)
            result.comment = stdout + stderr

        self._data.append(result)
        return result

    def run(self, cmd, test_ignore=False, post_hook=None, data=None, **options):
        '''Executes cmd using salt.utils run_all function.

        Fake results are returned instead of executing the command if test
        mode is enabled.
        '''
        if __opts__['test'] and not test_ignore:
            self.test()
            result = Result()
        else:
            if isinstance(cmd, list):
                cmd = ' '.join(cmd)

            result = Result(**__salt__['cmd.run_all'](cmd, runas='user', output_loglevel='quiet', **options))
            result.pop('pid', None)

        self._run_post_hook(post_hook, cmd, result, data)

        cmd_options = str(options) if options else ''
        cmd_string = '{0} {1}'.format(cmd, cmd_options)

        return self.save_result(result, message=cmd_string)

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

    # XXX: Not used; remove
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

    # XXX: Move formatting functions to Result
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
        comment = ''
        message = ''
        changes = {}
        mode = 'last' if 'last' in self.args.result_mode else 'all'
        debug = True if 'debug' in self.args.result_mode else False
        debug_changes = True if 'debug-changes' in self.args.result_mode else False

        index = retcode = 0
        if mode in ['last']:
            result = self._data[-1]
            retcode = result.retcode
            if result.result is not None:
                retcode = result.result
            if result.passed():
                index = -1

        if debug:
            index = 0

        # ----------------------------------------------------------------------
        # Determine 'retcode' and merge 'comments' and 'changes'
        # ----------------------------------------------------------------------
        for result in self._data[index:]:
            # 'comment' - Merge comment
            if result.comment.strip():
                comment += self.linefeed(comment) + result.comment

            # 'retcode' - Determine retcode
            # Use 'result' over 'retcode' if result is not None as 'retcode'
            # reflects last run state, where 'result' is set explicitly
            if result.result is not None:
                retcode = result.result
            elif result.retcode and mode in ['all']:
                retcode = result.retcode

            # 'changes' - Merge changes
            if result.changes and result.passed() and (debug_changes or not __opts__['test']):
                name = result.get('name', None) or self.__virtualname__
                changes.setdefault(name, {})
                for key, value in result.changes.items():
                    changes[name][key] = value

        # ----------------------------------------------------------------------
        # Combine 'message' + 'comment'
        # ----------------------------------------------------------------------
        if msg_all:
            message += msg_all
        elif msg_passed and not retcode:
            message += self.linefeed(message) + msg_passed
        elif msg_failed and retcode:
            message += self.linefeed(message) + msg_failed

        # Only include last comment unless result failed
        if not debug and mode in ['last'] and not retcode:
            comment = result.comment

        message += self.linefeed(message) + comment

        return Result(
            name    = self.__virtualname__,
            retcode = retcode,
            comment = message,
            stdout  = result.stdout,
            stderr  = result.stdout,
            changes = changes,
        )


@_function_alias('check')
class _Check(_QVMBase):
    '''
    Check if a virtual machine exists::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.check <vmname> exists flags=[quiet]

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
            result.retcode = not result.retcode

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

        qubesctl qvm.state <vmname> running

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>

        # Optional Positional
        - state:                (status)|running|halted|transient|paused
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
        parser.add_argument('state', nargs='*', default='status', choices=('status', 'running', 'halted', 'transient', 'paused'), help='Check power state of virtual machine')

    def __call__(self):
        args = self.args

        # Check VM power state
        retcode = 0
        stdout = self.vm().get_power_state()
        power_state = stdout.strip().lower()

        if 'status' not in args.state:
            if power_state not in args.state:
                retcode = 1

        # Create result
        result = Result(
            retcode = retcode,
            data    = power_state,
            stdout  = stdout,
            stderr  = '',
            message = '{0} {1}'.format(self.__virtualname__, ' '.join(args.state))
        )

        # Merge results
        self.save_result(result=result)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('create')
class _Create(_QVMBase):
    '''
    Create a new virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.create <vmname> label=red template=fedora-21 flags=[proxy]

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
            if result.retcode:
                result.result = result.retcode

        # Confirm VM is absent
        absent_result = check(args.vmname, *['absent'], **{'run-post-hook': absent_post_hook})
        self.save_result(absent_result)
        if absent_result.failed():
            return self.results()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-create {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Confirm VM has been created (don't fail in test mode)
        if not __opts__['test']:
            self.save_result(check(args.vmname, *['exists']))

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('remove')
class _Remove(_QVMBase):
    '''
    Remove an existing virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.remove <vmname> flags=[just-db]

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

        # Remove 'shutdown' flag from argv as its not a valid qvm.clone option
        if '--shutdown' in self.arg_info['__argv']:
            self.arg_info['__argv'].remove('--shutdown')

    @classmethod
    def parser_arguments(cls, parser):
        # Optional Flags
        parser.add_argument('--just-db', action='store_true', help='Remove only from the Qubes Xen DB, do not remove any files')
        parser.add_argument('--shutdown', action='store_true', help='Shutdown / kill VM if its running')
        parser.add_argument('--quiet', action='store_true', help='Quiet')
        parser.add_argument('--force-root', action='store_true', help='Force to run, even with root privileges')

        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        # Check VM power state
        def is_halted():
            halted_result = state(args.vmname, *['halted'])
            self.save_result(result=halted_result)
            return halted_result

        args = self.args

        if not is_halted():
            if args.shutdown:
                # 'shutdown' VM ('force' mode will kill on failed shutdown)
                shutdown_result = self.save_result(shutdown(args.vmname, *['wait', 'force']))
                if shutdown_result.failed():
                    return self.results()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-remove {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Confirm VM has been removed (don't fail in test mode)
        if not __opts__['test']:
            self.save_result(check(args.vmname, *['absent']))

        # Returns the results 'data' dictionary and adds comments in 'test' mode
        return self.results()


@_function_alias('clone')
class _Clone(_QVMBase):
    '''
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.clone <vm-name> <target_name> [shutdown=true|false] [path=]

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
        # Check VM power state
        def is_halted():
            halted_result = state(args.vmname, *['halted'])
            self.save_result(result=halted_result)
            return halted_result

        args = self.args

        # Check if 'target' VM exists; fail if it does and return
        target_check_result = self.save_result(check(args.target, *['absent']))
        if target_check_result.failed():
            return self.results()

        if not is_halted():
            if args.shutdown:
                # 'shutdown' VM ('force' mode will kill on failed shutdown)
                shutdown_result = self.save_result(shutdown(args.vmname, *['wait', 'force']))
                if shutdown_result.failed():
                    return self.results()

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-clone {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Confirm VM has been cloned (don't fail in test mode)
        if not __opts__['test']:
            self.save_result(check(args.target, *['exists']))

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('prefs')
class _Prefs(_QVMBase):
    '''
    Set preferences for a virtual machine domain

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.prefs <vm_name> label=orange

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

        # Use 'all' result-mode to show all results
        if 'last' in self.args.result_mode:
            self.args.result_mode.remove('last')
        self.args.result_mode.append('all')

    @classmethod
    def parser_arguments(cls, parser):
        # XXX:
        # TODO: Need to make sure set contains a keyword AND value
        #

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
        if result.passed():
            result.changes.setdefault(data['key'], {})
            result.changes[data['key']]['old'] = data['value_old']
            result.changes[data['key']]['new'] = data['value_new']

    def __call__(self):
        args = self.args
        vm = self.vm()

        label_width = 19
        fmt="{{0:<{0}}}: {{1}}".format(label_width)

        if args.action in ['list', 'get', 'gry']:
            if args.action in ['list']:
                # ==============================================================
                # XXX: TODO: Find alternative to using `execfile` to obtain
                #            qvm-prefs properties
                #
                # runpy, execfile
                #
                import os
                import sys
                _locals = dict()
                _globals = dict()
                try:
                    execfile('/usr/bin/qvm-prefs', _globals,_locals)
                except NameError:
                    pass
                properties = _locals.get('properties', []).keys()
                # ==============================================================
            else:
                properties = self.arg_info['kwargs'].keys()

            for key in properties:
                # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
                key = key.replace('-', '_')

                value_current = getattr(vm, key, self.MARKER)
                value_current = getattr(value_current, 'name', value_current)

                if value_current == self.MARKER:
                    continue

                self.save_result(prefix='', message=fmt.format(key, value_current))
                continue

        else:
            for key, value_new in self.arg_info['kwargs'].items():
                # Qubes keys are stored with underscrores ('_'), not hyphens ('-')
                key = key.replace('-', '_')

                value_current = getattr(vm, key, self.MARKER)
                value_current = getattr(value_current, 'name', value_current)

                # Key does not exist in vm database
                if value_current == self.MARKER:
                    message = fmt.format(key, 'Invalid key!')
                    result = Result(retcode=1)
                    self.save_result(result, message=message)
                    continue

                # Value matches; no need to update
                if value_current == value_new:
                    message = fmt.format(key, value_current)
                    self.save_result(prefix='[SKIP] ', message=message)
                    continue

                # Execute command (will not execute in test mode)
                data = dict(key=key, value_old=value_current, value_new=value_new)
                cmd = '/usr/bin/qvm-prefs {0} --set {1} {2} "{3}"'.format(' '.join(self.arg_info['_argparse_flags']), args.vmname, key, value_new)
                result = self.run(cmd, data=data)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('service')
class _Service(_QVMBase):
    '''
    Manage a virtual machine domain services::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.service <vm-name> [action] [service-name]

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
        self.arg_options_create(argv_ordering=['flags', 'args', 'varargs', 'keywords'])
        super(_Service, self).__init__(vmname, *varargs, **kwargs)

        # Use 'all' result-mode to show all results
        if 'last' in self.args.result_mode:
            self.args.result_mode.remove('last')
        self.args.result_mode.append('all')

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

        # XXX: Test with CLI interface.
        #
        # Current YAML interface:
        #   qvm.service:
        #     - enable:
        #       - service1
        #       - service2
        #       - service3
        #     - disable:
        #       - service4
        #       - service5
        #
        # Current CLI interface:
        #   qubesctl qvm.service enable="service1 service2 service3" disable="service4 service5"
        #
        # Additional CLI interface??? (TODO)
        #
        #parser.add_argument('action', nargs='?', default='list', choices=('list', 'enable', 'disable', 'default'), help='Action to take on service')
        #parser.add_argument('service_names', nargs='*', default=[], help='List of Service names to reset')

        parser.add_argument('--list', nargs='*', help='List services')
        parser.add_argument('--enable', nargs='*', default=[], help='List of service names to enable')
        parser.add_argument('--disable', nargs='*', default=[], help='List of service names to disable')
        parser.add_argument('--default', nargs='*', default=[], help='List of service names to default')

    def run_post(self, cmd, result, data):
        '''Called by run to allow additional post-processing of results before
        the results get stored to self.stdout, etc
        '''
        if result.passed():
            result.changes.setdefault(data['key'], {})
            result.changes[data['key']]['old'] = data['value_old']
            result.changes[data['key']]['new'] = data['value_new']

    def __call__(self):
        def label(value):
            if value is True:
                return 'Enabled'
            elif value is False:
                return 'Disabled'
            elif value is None:
                return 'Absent'
            return value

        # action value map
        action_map = dict(
            enable  = True,
            disable = False,
            default = None
        )

        args = self.args
        current_services = self.vm().services

        # Return all current services if a 'list' only was selected
        if args.list is not None or not (args.enable or args.disable or args.default):
            for service_name, value in current_services.items():
                if value:
                    prefix = '[ENABLED]  '
                else:
                    prefix = '[DISABLED] '
                self.save_result(prefix=prefix, message=service_name)
            return self.results()

        # Remove duplicate service names; keeping order listed
        seen = set()
        for action in [args.default, args.disable, args.enable]:
            for value in action:
                if value not in seen:
                    seen.add(value)
                else:
                    action.remove(value)

        for action in ['enable', 'disable', 'default']:
            service_names = getattr(args, action, [])
            for service_name in service_names:
                value_current = current_services.get(service_name, None)
                value_new = action_map[action]

                # Value matches; no need to update
                if value_current == value_new:
                    message = 'Service already in desired state: {0} \'{1}\' = {2}'.format(action.upper(), service_name, label(value_current))
                    self.save_result(prefix='[SKIP] ', message=message)
                    continue

                # Execute command (will not execute in test mode)
                data = dict(key=service_name, value_old=label(value_current), value_new=label(value_new))
                cmd = '/usr/bin/qvm-service {0} --{1} {2}'.format(args.vmname, action, service_name)
                result = self.run(cmd, data=data)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('run')
class _Run(_QVMBase):
    '''
    Run an application within a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.run [options] <vm-name> [<cmd>]

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
            start_result = self.save_result(start(args.vmname, *['quiet', 'no-guid']))
            if start_result.failed():
                return self.results()

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

        qubesctl qvm.start <vm-name>

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
        # Prevents startup status showing as 'Transient'
        def start_guid():
            try:
                if not self.vm().is_guid_running():
                    self.vm().start_guid()
            except AttributeError:
                # AttributeError: CEncodingAwareStringIO instance has no attribute 'fileno'
                pass

        def is_running(message='', error_message=''):
            running_result = state(args.vmname, *['running'])
            self.save_result(result=running_result, retcode=running_result.retcode, message=message, error_message=error_message)
            return running_result

        def is_transient():
            # Start guid if VM is 'transient'
            transient_result = state(args.vmname, *['transient'])
            if transient_result.passed():
                if __opts__['test']:
                    message = '\'guid\' will be started since in \'transient\' state!'
                    self.save_result(result=transient_result, message=message)
                    return self.results()

                # 'start_guid' then confirm 'running' power state
                start_guid()
                return not is_running(error_message='\'guid\' failed to start!')
            return False

        args = self.args

        # No need to start if VM is already 'running'
        if is_running():
            return self.results()

        # 'unpause' VM if its 'paused'
        paused_result = state(args.vmname, *['paused'])
        if paused_result.passed():
            resume_result = unpause(args.vmname)
            self.save_result(result=resume_result, error_message='VM failed to resume from pause!')
            if not resume_result:
                return self.results()

        if is_transient():
            return self.results()

        # XXX: TODO:
        # Got this failure to start... need to make sure messages are verbose, so
        # try testing in this state again once we get around to testing this function
        # if ret == -1: raise libvirtError ('virDomainCreateWithFlags() failed', dom=self)
        # libvirt.libvirtError: Requested operation is not valid: PCI device 0000:04:00.0 is in use by driver xenlight, domain salt-testvm4

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-start {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Confirm VM has been started (don't fail in test mode)
        if not __opts__['test']:
            if is_transient():
                return self.results()

            is_running()

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('shutdown')
class _Shutdown(_QVMBase):
    '''
    Shutdown a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.shutdown <vm-name>

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
        def is_halted(message=''):
            halted_result = state(args.vmname, *['halted'])
            self.save_result(result=halted_result, retcode=halted_result.retcode, error_message=message)
            return halted_result

        def is_transient():
            # Kill if transient and 'force' option enabled
            transient_result = state(args.vmname, *['transient'])
            if transient_result.passed():
                modes = 'force' if args.force else ''
                modes += ' + ' if modes and args.kill else ''
                modes = 'kill' if args.kill else ''

                if __opts__['test']:
                    if force:
                        message = 'VM will be killed in \'transient\' state since {0} enabled!'.format(' + '.join(force))
                    else:
                        message = 'VM is \'transient\'. \'kill\' or \'force\' mode not enabled!'
                        transient_result.retcode = 1
                    self.save_result(result=transient_result, message=message)
                    return self.results()

                # 'kill' then confirm 'halted' power state
                cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
                result = self.run(cmd)
                #return not is_halted(message='\'guid\' failed to halt!')
                return not self.save_result(is_halted(message='\'guid\' failed to halt!'))
            return False

        args = self.args
        differ = ListDiffer(['force', 'kill'], self.arg_info['__flags'])
        force = list(differ.unchanged())

        # No need to start if VM is already 'halted'
        if is_halted():
            return self.results()

        # XXX: Should be calling unpause so this is not required
        # 'unpause' VM if its 'paused'
        paused_result = state(args.vmname, *['paused'])
        if paused_result.passed():
            if __opts__['test']:
                message = 'VM will be unpaused'
                self.save_result(message=message)
                return self.results()

            # 'unpause' VM then confirm 'halted' power state
            self.vm().unpause()
            halted = self.save_result(is_halted(message='VM failed to resume from pause!'))
            return self.results()

        if is_transient():
            return self.results()

        # Execute command (will not execute in test mode)
        if self.args.kill:
            cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
        else:
            cmd = '/usr/bin/qvm-shutdown {0}'.format(' '.join(self.arg_info['__argv']))
        result = self.run(cmd)

        # Confirm VM has been halted (don't fail in test mode)
        if not __opts__['test']:
            # Kill if still not 'halted' only if 'force' enabled
            if not is_halted() and args.force:
                cmd = '/usr/bin/qvm-kill {0}'.format(args.vmname)
                result = self.run(cmd)

            is_halted()

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('kill')
class _Kill(_QVMBase):
    '''
    Kills a virtual machine domain::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.kill <vmname>

    Valid actions:

    .. code-block:: yaml

        # Required Positional
        - name:                 <vmname>
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Kill, self).__init__(vmname, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Required Positional
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')

    def __call__(self):
        args = self.args
        self.arg_info['varargs'].append('kill')

        # 'kill' VM
        halted_result = shutdown(args.vmname, *self.arg_info['varargs'], **self.arg_info['kwargs'])

        # Returns the results 'data' dictionary
        self.save_result(result=halted_result)
        return self.results()


@_function_alias('pause')
class _Pause(_QVMBase):
    '''
    Pause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.pause <vm-name>

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
        def is_running(message=''):
            running_result = state(args.vmname, *['running', 'paused', 'transient'])
            self.save_result(result=running_result, retcode=running_result.retcode, error_message=message)
            return running_result

        # Can't pause VM if it's not running
        if not is_running():
            return self.results()

        if __opts__['test']:
            message = 'VM will be paused'
            self.save_result(message=message)
            return self.results()

        # Execute command (will not execute in test mode)
        self.vm().pause()

        paused_result = state(args.vmname, *['paused'])
        self.save_result(result=paused_result, retcode=paused_result.retcode)

        # Returns the results 'data' dictionary
        return self.results()


@_function_alias('unpause')
class _Unpause(_QVMBase):
    '''
    Unpause a virtual machine::

    CLI Example:

    .. code-block:: bash

        qubesctl qvm.unpause <vm-name>

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
        # Check VM power state
        def is_paused(message=''):
            paused_result = state(args.vmname, *['paused'])
            self.save_result(result=paused_result, retcode=paused_result.retcode, error_message=message)
            return paused_result

        args = self.args

        # Can't resume VM if it's not paused
        if not is_paused():
            return self.results()

        if __opts__['test']:
            message = 'VM will be resumed'
            self.save_result(message=message)
            return self.results()

        # Execute command (will not execute in test mode)
        self.vm().unpause()

        running_result = state(args.vmname, *['running'])
        self.save_result(result=running_result, retcode=running_result.retcode, error_message='VM failed to resume from pause!')

        # Returns the results 'data' dictionary
        return self.results()
