# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       qubes
:platform:      all

======================
Misc utility functions
======================
'''

import collections

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
                replace = _update(target.get(key, {}), value, create=create, allowed=allowed, append=append)
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


