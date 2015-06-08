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
