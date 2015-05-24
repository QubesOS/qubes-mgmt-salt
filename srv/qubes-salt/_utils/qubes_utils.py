# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

======================
Misc utility functions
======================

from qubes_utils import tostring as _tostring
from qubes_utils import tolist as _tolist
from qubes_utils import arg_info as _arg_info
from qubes_utils import get_fnargs as _get_fnargs
from qubes_utils import alias as _alias
from qubes_utils import function_alias as _function_alias
from qubes_utils import update as _update
'''

# Import python libs
import types
#import copy
import collections

from inspect import getargvalues, stack

# Salt libs
import salt.utils


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


def arg_info(keyword_flag_keys=None, argv_ordering=[], skip=[]):
    '''
    Returns dictionary of calling function's named arguments and values as well
    as option to put values from kwargs on argv stack to allow processing as
    optional vars. (add --before the values) and formats in requested ordering.

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

    skip:        Skip formatting for giving arg type;
                 example: ['varargs']
    '''
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
    info['__argv'] = []

    # Convert varargs to a list if it exists so it can be appened to
    if info['__varargs'] in locals_:
        locals_[info['__varargs']] = tolist(locals_[info['__varargs']])

    # Populate info with values from arg_info
    for arg_name in info['__args'] + [info['__varargs']]:
        if arg_name:
            info[arg_name] = locals_[arg_name]

    # Populate info keyword dictionary to proper locations
    info.setdefault(info['__keywords'], {})
    for key, value in locals_[info['__keywords']].items():
        if key in keyword_flag_keys:
            info['__flags'].extend(tolist(value))
        elif key in argv_ordering:
            #info.setdefault(key, [])
            #if isinstance(value, list):
            #    value = ' '.join(value)
            #info[key].append(tostring(value))
            info[key] = tostring(value)
        else:
            info[info['__keywords']][key] = value

    # argv_ordering processing
    for section in argv_ordering:
        pass

    # flags = optional argv flags
    for flag in info['__flags']:
        if isinstance(flag, str):
            if flag in skip:
                continue
            if 'flags' in skip:
                info['_argparse_flags'].append(flag)
            else:
                info['_argparse_flags'].append('--{0}'.format(flag))
        #elif isinstance(flag, collections.Mapping):
        #    for key, value in flag.items():
        #        locals_[key] = tostring(value)
        #        locals_[info['__keywords']][key] = tostring(value)

    # args - positional argv
    if info['__args']:
        for value in info['__args']:
            # Get rid of any references to self
            if value ==  'self':
                continue
            info['_argparse_args'].append(tostring(info[value]))

    # *varargs - positional argv
    if info['__varargs']:
        for value in tolist(info[info['__varargs']]):
            # Ignore 'private' keywords
            if not value.startswith('__'):
                # Make keyword optional
                if 'varargs' in skip:
                    info['_argparse_varargs'].append(value)
                elif value.startswith('--'):
                    info['_argparse_varargs'].append(value)
                else:
                    info['_argparse_varargs'].append('--{0}'.format(value))

    # **kwargs = optional argv
    if info['__keywords']:
        for key, value in info[info['__keywords']].items():
            if key in keyword_flag_keys + skip:
                continue
            # Ignore 'private' keywords
            if not key.startswith('__'):
                if 'keywords' in skip or key.startswith('--'):
                    info['_argparse_keywords'].append(key)
                else:
                    info['_argparse_keywords'].append('--{0}'.format(key))
                if isinstance(value, list):
                    value = ' '.join(value)
                info['_argparse_keywords'].append(tostring(value))

    if not argv_ordering:
        argv_ordering = ['flags', 'keywords', 'args', 'varargs']
    for section in argv_ordering:
        # '_argparse_keywords', 'vmname'
        if '_argparse_{0}'.format(section) in info:
            section = '_argparse_{0}'.format(section)
        if section in info:
            if isinstance(info[section], list):
                info['__argv'].extend(info[section])
            else:
                info['__argv'].append(tostring(info[section]))

    return info


def get_fnargs(function, **kwargs):
    '''Returns all args that a function uses along with default values.
    '''
    args, fnargs = salt.utils.arg_lookup(function).values()
    for key, value in kwargs.items():
        if key in fnargs:
            fnargs[key] = value
    return fnargs


def alias(new_name):
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


def function_alias(new_name):
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
