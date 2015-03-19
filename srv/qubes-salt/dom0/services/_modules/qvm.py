# -*- coding: utf-8 -*-
'''
Manage Qubes settings
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


def arginfo(kwargs_list=None):
    '''
    Returns dictionary of calling function's named arguments and values as well
    as option to put values from kwargs on argv stack to allow processing as
    optional vars.
    '''
    frame = stack()[1][0]
    info = getargvalues(frame)._asdict()

    locals_ = info.pop('locals', {})
    info['__args'] = info.pop('args', ())
    info['__varargs'] = info.pop('varargs', ())
    info['__keywords'] = info.pop('keywords', ())
    info['__argv'] = []

    if kwargs_list and isinstance(kwargs_list, list) and info['__keywords'] and info['__keywords'] in locals_:
        for arg in kwargs_list:
            if arg not in locals_[info['__keywords']]:
                continue

            if not isinstance(locals_[info['__keywords']][arg],  list):
                continue

            # Remove from locals_ stack and reference to kwarg_item
            kwargs_item = locals_[info['__keywords']].pop(arg)

            # Make sure varargs objects exist
            if not info['__varargs']:
                info['__varargs'] = ('varargs')
                locals_[info['__varargs']] = []

            for item in kwargs_item:
                if isinstance(item, str):
                    locals_[info['__varargs']].append('--{0}'.format(item))
                elif isinstance(item, collections.Mapping):
                    for key, value in item.items():
                        locals_[key] = value
                        locals_[info['__keywords']][key] = value

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
            info['__argv'].append(info[name])

    # *varargs - positional argv
    if info['__varargs']:
        info['__argv'].extend(tolist(info[info['__varargs']]))

    # **kwargs = optional argv
    if info['__keywords']:
        for name, value in info[info['__keywords']].items():
            # Ignore 'private' keywords
            if not name.startswith('__'):
                # Make keyword optional
                if name.startswith('--'):
                    info['__argv'].append(name)
                else:
                    info['__argv'].append('--{0}'.format(name))
                info['__argv'].append(value)

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
        def wrapper(*args, **kwds):
            module = func(*args, **kwds)
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


def tolist(value):
    '''Converts value to a list.
    '''
    if not value:
        value = []
    elif isinstance(value, str):
        value = [value,]
    return value


def _get_vm(vmname):
    return _VMAction.get_vm(vmname)


def _run_all(cmd):
    if isinstance(cmd, list):
        cmd = ' '.join(cmd)

    result = __salt__['cmd.run_all'](cmd, runas='user', output_loglevel='quiet')
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
        if not vm:
            raise CommandExecutionError('Error! No VM found with the name of: {0}'.format(values))

        setattr(namespace, self.dest, values)
        setattr(namespace, 'vm', vm)


class _ModuleHelper(object):
    '''Module Helper is meant to be sub-classed and contains code pieces that
       would otherwise be duplicated.
    '''
    def __init__(self, arginfo):
        self.arginfo = arginfo
        self.ret = {'retcode': 0, 'changes': {},}
        self.stdout = ''
        self.stderr = ''

    @classmethod
    def _parser(cls):
        '''
        Implement in sub-class.
        '''
        return None

    @classmethod
    def usage(cls):
        parser = cls._parser()
        if not parser:
            return cls.__doc__
        else:
            usage_header = '=== USAGE ' + '='*70 + '\n'
            doc_header = '=== DOCS ' + '='*71 + '\n'
            return '{0}{1}\n{2}{3}'.format(doc_header, cls.__doc__, usage_header, parser.format_help())

    def run(self, cmd):
        '''Executes cmd using salt.utils run_all function.

        Fake results are returned instead of executing the command if test
        mode is enabled.
        '''
        if __opts__['test']:
            result = ret
            result['retcode'] = None
        else:
            result = _run_all(cmd)
            if result['retcode']:
                self.stderr += '{0}:\n{1}\n'.format(result['stderr'], cmd)

        result.setdefault('changes', {})
        return result

    def results(self):
        '''Returns the 'ret' (results) dictionary.
        '''
        self.ret['stdout'] = self.stdout
        self.ret['stderr'] = self.stderr
        return self.ret


def check(vmname):
    '''
    Check if a virtual machine exists::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.check <vm-name>
    '''
    cmd = "/usr/bin/qvm-check {0}".format(vmname)
    return _run_all(cmd)


def state(vmname):
    '''
    Return virtual machine state::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.state <vm-name>
    '''
    ret = {}

    vm = _get_vm(vmname)
    if not vm:
        return check(vmname)

    ret['stdout'] = vm.get_power_state()
    ret['retcode'] = not vm.is_guid_running()
    return ret


def create(vmname,
           template=None,
           label=None,
           proxy=None,
           hvm=None,
           hvm_template=None,
           net=None,
           standalone=None,
           root_move_from=None,
           root_copy_from=None,
           mem=None,
           vcpus=None,
           internal=None):
    '''
    Create a new virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.create <vm-name> label=red template=fedora-20-x64
    '''
    # Check if an existing VM already exists with same name and fail if so
    ret = check(vmname)
    if not ret['retcode']:
        ret['retcode'] = 1
        return ret

    cmd = ['/usr/bin/qvm-create']
    args, fnargs = salt.utils.arg_lookup(create).values()
    for arg in fnargs:
        value = locals().get(arg, None)
        if value:
            arg = '--' + arg.replace('_', '-')
            cmd.extend([arg, str(value)])
    cmd.append(vmname)

    ret = _run_all(cmd)
    return ret


def remove(vmname, just_db=None):
    '''
    Remove an existing virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.remove <vm-name> [just_db=True]
    '''
    # Make sure the VM exists, otherwise fail
    ret = check(vmname)
    if ret['retcode']:
        return ret

    cmd = ['/usr/bin/qvm-remove']
    args, fnargs = salt.utils.arg_lookup(remove).values()
    for arg in fnargs:
        value = locals().get(arg, None)
        if value:
            arg = '--' + arg.replace('_', '-')
            cmd.extend([arg, str(value)])
    cmd.append(vmname)

    ret = _run_all(cmd)
    return ret


def clone(vmname,
          target,
          label=None,
          path=None):
    '''
    Clone a new virtual machine::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.clone <vm-name> <target_name> [path=]
    '''
    # Check if an existing VM already exists with same name and fail if so
    ret = check(target)
    if not ret['retcode']:
        ret['retcode'] = 1
        return ret

    cmd = ['/usr/bin/qvm-clone']
    args, fnargs = salt.utils.arg_lookup(create).values()
    for arg in fnargs:
        value = locals().get(arg, None)
        if value:
            arg = '--' + arg.replace('_', '-')
            cmd.extend([arg, str(value)])
    cmd.append(vmname)
    cmd.append(target)

    ret = _run_all(cmd)
    return ret


def get_prefs(vmname):
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


def prefs(vmname,
          include_in_backups=MARKER,
          pcidevs=MARKER,
          label=MARKER,
          netvm=MARKER,
          maxmem=MARKER,
          memory=MARKER,
          kernel=MARKER,
          template=MARKER,
          vcpus=MARKER,
          kernelopts=MARKER,
          name=MARKER,
          drive=MARKER,
          mac=MARKER,
          debug=MARKER,
          default_user=MARKER,
          qrexec_installed=MARKER,
          guiagent_installed=MARKER,
          seamless_gui_mode=MARKER,
          qrexec_timeout=MARKER,
          timezone=MARKER,
          internal=MARKER,
          autostart=MARKER):
    '''
    Set preferences for vm target

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.set_prefs <vm_name> label=orange

    Calls the qubes utility directly since the currently library really has
    no validation routines whereas the script does.
    '''
    ret = {'retcode': 0, 'changes': {},}
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

            if result['retcode']:
                ret['retcode'] = result['retcode']
                stderr += '{0}: {1}\n{2}'.format(key, value, result['stderr'])
            else:
                ret['changes'][key] = {}
                ret['changes'][key]['old'] = current_state[key]
                ret['changes'][key]['new'] = value
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
    Manage virtual machine services::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.service <vm-name> [action] [service-name]

    Valid actions: list, enable, disable, default
    '''
    def __init__(self, vmname, *varargs, **kwargs):
        '''
        '''
        super(_Service, self).__init__(arginfo())
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        print self.args
        print

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.service')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
        parser.add_argument('action', nargs='?', default='list', choices=('list', 'enable', 'disable', 'default'), help='Action to take on service')
        parser.add_argument('service_names', nargs='*', default=[], help='List of Service names to reset')
        return parser

    def __call__(self):
        args = self.args
        current_services = args.vm.services

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
                    self.ret['changes'][service_name]['old'] = current_services[service_name]
                    self.ret['changes'][service_name]['new'] = updated_services[service_name]
                    self.stdout += result['stdout'] + '\n'
                else:
                    self.stdout += '{0} "{1}" service is already in desired state: {2}\n'.format(args.vmname, service_name, updated_services.get(service_name, 'missing'))

        # Returns the 'ret' dictionary
        return self.results()


@_function_alias('start')
class _Start(_ModuleHelper):
    '''
    Manage virtual machine services::

    CLI Example:

    .. code-block:: bash

        salt '*' qvm.start <vm-name>

    Valid actions:

    .. code-block:: yaml

        - name:                 <vmname>
        - options:
          - drive:              <DRIVE>
          - hddisk:             <DRIVE_HD>
          - cdrom:              <DRIVE_CDROM>
          - custom-config:      <CUSTOM_CONFIG>
          - tray
          - no-guid
          - dvm
          - debug
          - install-windows-tools
    '''
    def __init__(self, vmname, **kwargs):
        '''
        '''
        # Tell arginfo to also add options values to argv; will remove options
        # from argv, only converting the values
        super(_Start, self).__init__(arginfo(['options']))
        self.parser = self._parser()
        self.args = self.parser.parse_args(args=self.arginfo['__argv'])

        print self.args
        print

    @classmethod
    def _parser(cls):
        parser = _ArgumentParser(prog='qvm.start')
        parser.add_argument('vmname', action=_VMAction, help='Virtual machine name')
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

        current_check =  check(args.vmname)
        if current_check['retcode']:
            return current_check

        current_state =  state(args.vmname)
        if 'Halted' not in current_state['stdout']:
            current_state['retcode'] = 1
            return current_state

        # Execute command (will not execute in test mode)
        cmd = '/usr/bin/qvm-start {0}'.format(' '.join(self.arginfo['__argv']))
        result = self.run(cmd)

            # Attempt to predict result in test mode
        if __opts__['test']:
            result['stdout'] = 'Virtual Machine will be started'
            result['stderr'] = ''

        # Returns the 'ret' dictionary
        return self.results()
