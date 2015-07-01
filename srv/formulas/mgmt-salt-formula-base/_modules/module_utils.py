# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

================
Module Utilities
================
'''

# Import python libs
import types
import copy
import argparse
import logging
import collections

from inspect import getargvalues, stack

# Salt libs
import salt.config
import salt.loader
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Salt + Qubes libs
from qubes_utils import (
    Status, tostring, tolist
)

# Enable logging
log = logging.getLogger(__name__)

# Used to identify values that have not been passed to functions which allows
# the function modules not to have to know anything about the default types
# excpected
try:
    if MARKER:
        pass
except NameError:
    MARKER = object()

try:
    __context__['module_utils_loaded'] = True
except NameError:
    __context__ = {}


class ArgparseFunctionWrapper(object):
    '''Wraps functions to appear as string.

    Argparse only alllows file, str or int types so to be able to use argparse
    to parse other types, they can be wrapped and will appear as 'None'

    Function is still callable
    '''
    def __init__(self, func):
        self.func = func
    def __len__(self):
        return 0
    def __call__(self, *varargs, **kwargs):
        self.func(*varargs, **kwargs)


def arg_info(parser, info=None, keyword_flag_keys=None, argv_ordering=[], skip=[]):
    '''
    Returns dictionary of calling function's named arguments and values as well
    as option to put values from kwargs on argv stack to allow processing as
    optional vars. (add --before the values) and formats in requested ordering.

    parser:     argparser instance
    keyword_flag_keys: Provide a keys in list that are available in kwargs to place
                treat those values as varargs
                example:
                ['flags'] - Any vaules contained in kwargs['flags'], will
                be handled as varargs

    argv_ordering: Create alternate `argv` format
                default:
                    ['varargs', 'keywords', 'args']
                example:
                    ['varargs', 'keywords', 'args', 'cmd']

    skip:       Skip formatting for giving arg type;
                example: ['varargs']
    '''
    if not info:
        frame = stack()[1][0]
        info = getargvalues(frame)._asdict()

    locals_ = info.pop('locals', {})
    info['__args'] = info.pop('args', None)
    info['__varargs'] = info.pop('varargs', None)
    info['__keywords'] = info.pop('keywords', None)
    info['__flags'] = []
    info['_argparse_args'] = []
    info['_argparse_varargs'] = []
    info['_argparse_keywords'] = []
    info['_argparse_flags'] = []
    info['_argparse_skipped'] = []
    info['__argv'] = []

    # Convert varargs to a list if it exists so it can be appened to
    if info['__varargs'] in locals_:
        locals_[info['__varargs']] = tolist(locals_[info['__varargs']])

    # Copy 'args' values and 'varargs' list to 'info' dictionary
    for arg_name in info['__args'] + [info['__varargs']]:
        if arg_name:
            info[arg_name] = locals_[arg_name]

    # Create a positionals list
    positionals = []
    for action in parser._get_positional_actions():
        positionals.append(action.dest)
    info['_argparse_args'] = [MARKER] * len(positionals)

    # args - positional argv
    index_args = 0
    if info['__args']:
        for value in info['__args']:
            # Get rid of any references to self
            if value ==  'self':
                continue
            info['_argparse_args'][index_args] = tostring(info[value])
            index_args += 1

    # Populate info keyword dictionary to proper locations
    info.setdefault(info['__keywords'], {})
    for key, value in locals_[info['__keywords']].items():
        if key in keyword_flag_keys:
            info['__flags'].extend(tolist(value))
        elif key.replace('-', '_') in positionals:
            key = key.replace('-', '_')
            index = positionals.index(key)
            positionals[index] = key
            info['_argparse_args'][index] = value
            info[key] = value
        elif key in argv_ordering:
            info[key] = tostring(value)
        else:
            info[info['__keywords']][key] = value

    # XXX: Trim _argparse_vars
    info['_argparse_args'] = [v for i, v in enumerate(info['_argparse_args']) if v != MARKER]

    # *varargs - positional argv
    if info['__varargs']:
        for value in tolist(info[info['__varargs']]):
            info['_argparse_varargs'].append(value)

    # flags = optional argv flags
    for flag in info['__flags']:
        if isinstance(flag, str):
            if flag in skip:
                continue
            if 'flags' in skip:
                info['_argparse_flags'].append(flag)
            else:
                info['_argparse_flags'].append('--{0}'.format(flag))

    # **kwargs = optional argv
    if info['__keywords']:
        for key, value in info[info['__keywords']].items():
            #if key in keyword_flag_keys:
            if key in keyword_flag_keys + positionals:
                continue

            section = '_argparse_keywords'
            if key in skip:
                info[info['__keywords']].pop(key, None)
                section = '_argparse_skipped'

            # Ignore 'private' keywords
            if not key.startswith('__'):
                if 'keywords' in skip or key.startswith('--'):
                    info[section].append(key)
                else:
                    info[section].append('--{0}'.format(key))

                if isinstance(value, list) and value:
                    info[section].extend(value)
                elif isinstance(value, types.FunctionType):
                    info[section].append(ArgparseFunctionWrapper(value))
                else:
                    info[section].append(tostring(value))

    # argv ordering
    if not argv_ordering:
        argv_ordering = ['flags', 'keywords', 'args', 'varargs']
    for section in argv_ordering:
        # '_argparse_keywords', 'name'
        if '_argparse_{0}'.format(section) in info:
            section = '_argparse_{0}'.format(section)

        if section in info:
            if isinstance(info[section], list):
                info['__argv'].extend(info[section])
            elif isinstance(info[section], types.FunctionType):
                info['__argv'].append(info[section])
            else:
                info['__argv'].append(tostring(info[section]))

    return info


class ArgumentParser(argparse.ArgumentParser):
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


class ModuleBase(object):
    '''ModuleBase is a base class which contains base functionality and utility
       to implement the qvm-* commands
    '''
    MARKER = object()

    @staticmethod
    def find_key(adict, text):
        '''
        Attempt to find a key in dictionary that may have the format of
        'this-is-a-key', compared to 'this_is_a_key'.
        '''
        for key in adict.keys():
            if key.replace('-', '_') == text:
                return key
        return None

    def _set_debug_mode(self):
        __context__.setdefault('debug', [])

        if self.args.debug_mode is not None:
            if self.args.debug_mode:
                if 'debug' not in self.args.status_mode:
                    self.args.status_mode.append('debug')
                if self.__virtualname__ not in __context__['debug']:
                    __context__['debug'].append(self.__virtualname__)
            else:
                if 'debug' in self.args.status_mode:
                    self.args.status_mode.remove('debug')
                if self.__virtualname__ in __context__['debug']:
                    __context__['debug'].remove(self.__virtualname__)
        elif self.__virtualname__ in __context__['debug'] or '__all__' in __context__['debug']:
            if 'debug' not in self.args.status_mode:
                self.args.status_mode.append('debug')

        self._debug_mode = __context__['debug']

    def __init__(self, *varargs, **kwargs):
        # XXX: NEW - see if we can't remove this; can't functions use info['varargs']...
        self.varargs = varargs
        self.kwargs = kwargs

        self._data = []

        if not hasattr(self, 'arg_options'):
            self.arg_options = self.arg_options_create()
        self.__info__ = getattr(self, '__info__', None)

        self.parser = self._parser()
        for group in self.parser._action_groups:
            if group.title == 'default':
                for action in group._group_actions:
                    option = self.find_key(kwargs, action.dest) or action.dest.replace('_', '-')
                    self.arg_options['skip'].append(option)

        self.arg_info = arg_info(self.parser, info=self.__info__, **self.arg_options)
        argv = self.arg_info['_argparse_skipped'] + ['--defaults-end'] + self.arg_info['__argv']
        self.args = self.parser.parse_args(args=argv)

        # Type of status mode to use (default: last)
        if 'last' not in self.args.status_mode and 'all' not in self.args.status_mode:
            self.args.status_mode.append('last')

        # Set debug mode
        self._set_debug_mode()

    @classmethod
    def _parser_arguments_default(cls, parser):
        '''Default argparse definitions.
        '''
        # Initial status_mode options
        parser.add_argument('--status-mode', nargs='*', default=['last'], choices=('last', 'all', 'debug'), help=argparse.SUPPRESS)

        # Run command post process hook function
        parser.add_argument('--run-post-hook', action='store', help=argparse.SUPPRESS)

        # Initial debug_mode options
        parser.add_argument('--debug-mode', action='store', type=bool, default=None, help=argparse.SUPPRESS)

        # Does nothing; just a marker to signal end of defaults
        parser.add_argument('--defaults-end', action='store_true', default=True, help=argparse.SUPPRESS)

    @classmethod
    def _parser(cls):
        '''Argparse Parser.
        '''
        default_parser = ArgumentParser(add_help=False)

        # Add default parser arguments
        default = default_parser.add_argument_group('default')
        cls._parser_arguments_default(default)

        # XXX: How to include both formatters; a list breaks it
        #                        formatter_class=[argparse.ArgumentDefaultsHelpFormatter,
        #                                         argparse.RawDescriptionHelpFormatter],

        # Add sub-class parser arguments
        parser = ArgumentParser(prog=cls.__virtualname__,
                                parents=[default_parser],
                                add_help=False,
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                conflict_handler='resolve',
                                description=cls.__doc__)
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
            #usage_header = '=== USAGE ' + '='*70 + '\n'
            #doc_header = '=== DOCS ' + '='*71 + '\n'
            #return '{0}{1}\n{2}{3}'.format(doc_header, cls.__doc__, usage_header, parser.format_help())
            return parser.format_help()

    def arg_options_create(self, keyword_flag_keys=None, argv_ordering=None, skip=None):
        '''Default arg_info options.
        '''
        data = {}
        data['keyword_flag_keys'] = keyword_flag_keys or ['flags']
        data['argv_ordering'] = argv_ordering or ['flags', 'keywords', 'args', 'varargs']
        data['skip'] = skip or []

        self.arg_options = copy.deepcopy(data)
        return self.arg_options

    def save_status(self, status=None, retcode=None, result=None, data=None, prefix=None, message='', error_message=''):
        '''Merges data from individual status into master data dictionary
        which will be returned and includes all changes and comments as well
        as the overall status status
        '''
        # Create a default status if one does not exist
        if status is None:
            status = Status()

        if not status.name:
            status.name = self.__virtualname__

        status._format(retcode=retcode, result=result, data=data, prefix=prefix, message=message, error_message=error_message)
        self._data.append(status)

        return status

    def run(self, cmd, test_ignore=False, post_hook=None, data=None, **options):
        '''Executes cmd using salt.utils run_all function.

        Fake status are returned instead of executing the command if test
        mode is enabled.
        '''
        if __opts__['test'] and not test_ignore:
            status = Status(retcode=0, prefix='[TEST] ')
        else:
            if isinstance(cmd, list):
                cmd = ' '.join(cmd)

            status = Status(**__salt__['cmd.run_all'](cmd, runas='user', output_loglevel='quiet', **options))
            status.pop('pid', None)

        self._run_post_hook(post_hook, cmd, status, data)

        cmd_options = str(options) if options else ''
        cmd_string = '{0} {1}'.format(cmd, cmd_options)

        return self.save_status(status, message=cmd_string)

    def _run_post_hook(self, post_hook, cmd, status, data):
        '''Execute and post hooks if they exist.
        '''
        self.run_post(cmd, status, data)
        if post_hook:
            post_hook(cmd, status, data)
        if self.args.run_post_hook:
            self.args.run_post_hook(cmd, status, data)

    def run_post(self, cmd, status, data):
        '''Called by run to allow additional post-processing of status before
        the status get stored to self.stdout, etc

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

    def status(self):
        '''Returns finalized merged 'data' status.
        '''
        status_mode = 'last' if 'last' in self.args.status_mode else 'all'
        cli_mode = True if '__pub_fun' in self.kwargs else False
        debug_mode = True if 'debug' in self.args.status_mode else False

        status = Status()
        return status._finalize(data=self._data, status_mode=status_mode, cli_mode=cli_mode, debug_mode=debug_mode, test_mode=__opts__['test'])
