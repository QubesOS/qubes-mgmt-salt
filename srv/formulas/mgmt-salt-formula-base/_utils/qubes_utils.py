# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

======================
Misc Utility Functions
======================
'''

# Import python libs
import sys
import types
import collections
import logging

from inspect import stack

# Salt libs
import salt.config
import salt.loader
import salt.pillar
import salt.utils
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Third party libs
from options import Options

# Enable logging
log = logging.getLogger(__name__)

## Set salt pillar, grains and opts settings so they can be applied to modules
##
##__opts__ = salt.config.minion_config('/etc/salt/minion')
##__opts__['grains'] = salt.loader.grains(__opts__)
##pillar = salt.pillar.get_pillar(
##    __opts__,
##    __opts__['grains'],
##    __opts__['id'],
##    __opts__['environment'],
##)
##__opts__['pillar'] = pillar.compile_pillar()
##__salt__ = salt.loader.minion_mods(__opts__)
##__grains__ = __opts__['grains']
##__pillar__ = __opts__['pillar']


class Status(Options):
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
        super(Status, self).__init__(*args, **defaults)

    def __len__(self):
        return self.passed()

    def reset(self, key, default=None):
        value = getattr(self, key, default)
        self[key] = type(self[key])()
        return value

    # - 'result' or 'retcode' are the indicators of a successful status
    # - If 'result' is not None that value is used and 'retcode' ignored
    #   which allows retcode to be overridden if needed.  If 'result' is None
    #   the value from 'retcode' is used to determine a pass or fail.
    #
    # 'retcode': 0 == pass / 1+ == fail (usually a shell return code)
    # 'result':  True == pass / False == fail / None == Unused
    def passed(self, **kwargs):
        return self.result if self.result is not None else not bool(self.retcode)

    def failed(self, **kwargs):
        return not self.result if self.result is not None else bool(self.retcode)

    def _format(self, name=None, retcode=None, result=None, data=None, prefix=None, message='', error_message=''):
        '''Combines argument variables and formats the status.
        '''
        # Copy args to status. Passed args override status set args
        args = ['name', 'retcode', 'result', 'data', 'prefix', 'message', 'error_message']
        for arg in args:
            if arg not in self or locals().get(arg, None):
                self[arg] = locals()[arg]

        if not self.comment:
            # ------------------------------------------------------------------
            # Create comment
            # ------------------------------------------------------------------
            prefix = self.prefix if 'prefix' in self else ''
            message = self.message if 'message' in self else ''
            error_message = self.error_message if 'error_message' in self else ''

            if prefix is None:
                prefix = '[FAIL] ' if self.failed() else '[PASS] '
            indent = ' ' * len(prefix)

            # Manage message
            if self.failed():
                if error_message:
                    message = error_message
            if not message:
                indent = ''
                message = message.strip()

            stdout = stderr = ''
            if self.failed() and self.stderr.strip():
                if message:
                    stderr += '{0}{1}'.format(prefix, message)
                if self.stdout.strip():
                    stderr += '\n{0}{1}'.format(indent, self.stdout.strip().replace('\n', '\n' + indent))
                if self.stderr.strip():
                    stderr += '\n{0}{1}'.format(indent, self.stderr.strip().replace('\n', '\n' + indent))
            else:
                if message:
                    stdout += '{0}{1}'.format(prefix, message)
                if self.stdout.strip():
                    stdout += '\n{0}{1}'.format(indent, self.stdout.strip().replace('\n', '\n' + indent))

            if stderr:
                if stdout:
                    stdout = '====== stdout ======\n{0}\n\n'.format(stdout)
                stderr = '====== stderr ======\n{0}'.format(stderr)
            self.comment = stdout + stderr

            return self

    def _finalize(self, data=[], status_mode='last', cli_mode=False, debug_mode=False, test_mode=False):
        '''Merges provided list of status and prepares status
        for return to salt.

        Additional messages may be appended to stdout

        data:
            List of status to merge

        status_mode:
            all or last. last only uses last retcode to determine overall
            success where all will fail on first failure code

        cli_mode:
            True if called by commandline interface, otherwise false

        debug_mode:
            Merges all status messages

        test_mode:
            True if test mode is enabled, otherwise false
        '''
        def linefeed(text):
            return '\n' if text else ''

        comment = ''
        message = ''
        changes = {}

        if not data:
            data = [self]

        index = retcode = 0
        if status_mode in ['last']:
            status = data[-1]
            retcode = status.retcode
            if status.result is not None:
                retcode = not status.result
            if status.passed():
                index = -1

        if debug_mode:
            index = 0

        # ----------------------------------------------------------------------
        # Determine 'retcode' and merge 'comments' and 'changes'
        # ----------------------------------------------------------------------
        for status in data[index:]:
            # 'comment' - Merge comment
            if status.comment.strip():
                comment += linefeed(comment) + status.comment

            # 'retcode' - Determine retcode
            # Use 'result' over 'retcode' if result is not None as 'retcode'
            # reflects last run state, where 'result' is set explicitly
            if status.result is not None:
                retcode = not status.result
            elif status.retcode and status_mode in ['all']:
                retcode = status.retcode

            if status.result and test_mode:
                status.result = None
            elif test_mode:
                status.result = None if not retcode else False
            else:
                status.result = True if not retcode else False

            # 'changes' - Merge changes
            if status.changes and status.passed():
                name = status.get('name', '')  # or self.__virtualname__
                changes.setdefault(name, {})
                for key, value in status.changes.items():
                    changes[name][key] = value

        # Only include last comment unless status failed
        if not debug_mode and status_mode in ['last'] and not retcode:
            comment = status.comment

        # If called by CLI only return stdout
        if cli_mode:
            return dict(
                retcode = retcode,
                stdout  = status.stdout or comment,
                stderr  = status.stdout,
            )

        # XXX: Could now just update self and return self, but may need to
        #      make sure attrs are cleared first?
        return Status(
            name    = status.name,
            retcode = retcode,
            result = status.result,
            comment = comment,
            stdout  = status.stdout,
            stderr  = status.stdout,
            changes = changes,
        )


def tostring(value):
    '''Convert value to string when possible (for argparse)
    '''
    if value is None:
        value = ''
    elif isinstance(value, types.ListType):
        value = ' '.join(value)
    else:
        value = str(value)

    return value


def tolist(value):
    '''Converts value to a list.
    '''
    if not value:
        value = []
    elif isinstance(value, str):
        value = [value,]
    elif isinstance(value, tuple):
        value = list(value)
    return value


def get_fnargs(function, **kwargs):
    '''Returns all args that a function uses along with default values.
    '''
    args, fnargs = salt.utils.arg_lookup(function).values()
    for key, value in kwargs.items():
        if key in fnargs:
            fnargs[key] = value
    return fnargs


def function_alias(new_name):
    '''
    Creates a generated function alias that initializes decorator class then calls
    the instance and returns any values.

    Doc strings are also copied to wrapper so they are available to salt command
    line interface via the --doc option.
    '''
    def outer(func):
        frame = stack()[0][0]
        func_globals = frame.f_back.f_globals

        if '__virtualname__' in func_globals:
            func.__virtualname__ = '{0}.{1}'.format(func_globals['__virtualname__'], new_name)

        def wrapper(*varargs, **kwargs):
            module = func(*varargs, **kwargs)
            return module()
        wrapper.func = func

        if 'usage' in dir(func):
            wrapper.__doc__ = func.usage()
        else:
            wrapper.__doc__ = func.__doc__

        wrapper.__name__ = new_name
        func_globals_save = {new_name: wrapper}
        func_globals.update(func_globals_save)
        return func
    return outer


def update(target, source, create=False, allowed=None, append=False):
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
                replace = update(target.get(key, {}), value, create=create, allowed=allowed, append=append)
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
