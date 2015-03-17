# -*- coding: utf-8 -*-

# YAMLSCRIPT INSTALLATION NOTES:
# ------------------------------
#   - This file must go in the _renderers directory:
#     (/srv/salt/_renderer/yamlscript.py)
#     (/srv/salt/_renderer/yamlscript_utils.py)
#
#   - Then need to sync renderers before it can be used:
#     - salt-call --local saltutil.sync_renderers
#       -- OR --
#     - salt-call --local state.highstate
#
# DEBUGGING NOTES:
# ----------------
#   - Just soft link the 2 files from /src/salt/renderers directory so breakpoints
#     can be set.
#   - Also soft link the files in /var/cache/salt/minion/extmods/renderers
#     source code location as well (salt-formula)

from __future__ import absolute_import  # So yaml can be imported

import re
import logging
import sys
import copy
import collections
import exceptions
import traceback
import pprint
import json
import StringIO

import salt.fileclient
import salt.client
import salt.renderers.pyobjects
import salt.utils.serializers.yaml
import salt.utils.odict
import salt.utils
import salt.template
from salt.exceptions import SaltRenderError
from salt.utils.yamlloader import SaltYamlSafeLoader

import voluptuous
from voluptuous import (MultipleInvalid,
                        Invalid,
                        Required,
                        Any,
                        Coerce,
                        # All,
                        # Msg,
                        # Lower
                        )

log = logging.getLogger(__name__)


class Schema(object):
    '''
    Checks schema of objects.
    Will raise a RenderError if schema is not correct
    Will coerce data where applicable as well as return defaults
    where no values were supplied
    '''

    @classmethod
    def coerce_to_list(cls, type, msg=None):
        """
        Convert a value into a list.
        """
        # pylint: disable=W0622, C0103
        def f(v):
            if isinstance(v, type):
                return [v]
            else:
                raise Invalid(msg or ('expected %s' % type.__name__))

        return f

    @classmethod
    def schema(cls, data, schema, index):
        schema = voluptuous.Schema(schema)
        try:
            return schema(data)
        except MultipleInvalid as error:
            raise RenderError(str(error), error.path[-1], index=index)

    @classmethod
    def pillars(cls, data=None, index=None):
        '''
        $pillars declaration needs to be before any other yaml or python

        $pillars:
          auto: True|(False)
          disabled:
            - <state_id>
            - <state_id>
          enabled:
            - <state_id>
            - <state_id>: <pillar_id>
          aliases:
            - <state_id>.<state_name>: None|<path>

        The `$pillars` declaration contains instructions on how to deal with
        merging pillar data into the state file.

        auto:
          True: Default. Will attempt to automatically merge pillar data for
                all state_id's.  A pillar_id with the same name as the state_id will
                need exist with the same yaml structure:
                  pillar_id:
                    pillar_name:
                      - values
                      - values
          False: No automatic attempt will be made to merge pillar data.

        enabled/disabled:
          Over-rides auto declaration.

          If auto is set to True/all any state_id's contained in `disabled`
          will not be merged, unless over-ridden by a state_data `__pillar__`
          directive.  `disabled` has no meaning if `auto` is False

          If auto is set to False any state_id's contained in `enabled` will
          attempt to be merged with pillar data, unless over-ridden by a
          state_data `__pillar__` directive.

          `enabled` also allows a map to specific a pillar_id that is not the
          same as the state_id.  Specify a mapped pillar_id like this:
          - state_id: pillar_id
          - http: apache

        aliases:
          Aliases allow shorter paths to the pillar data.  Normally, the
          pillar structure must be the same as state structure in able to
          automatically merge data.  In some cases this may not be desired
          so an alias may be set on a per state basis.

          Setting `path` to `None` will use root (base) of pillar_id.

          Typical structure:
          state_id:             pillar_id:
            state_name:           pillar_name:
            - state_data1  --->   - pillar_data1
            - state_data2  --->   - pillar_data2
          Aliased:
          state_id.state_name: None
          state_id.state_name:  pillar_id:
            - state_data1  --->   - pillar_data1
            - state_data2  --->   - pillar_data2

        __pillar__ declaration:
          A `__pillar__` declaration can be set in any state and will over
          ride `auto`, `disabled` and `enabled` declarations.
          state_id:
            state_name:
              __pillar__: True|False|<string>
          True: Will attempt to merge pillar data
          string: string value of the pillar_id to use (map)
          False: Will not attempt to merge pillar data

        __alias__ declaration:
          An `__alias__` declaration can be set to change the path to
          pillar_data.  Only the path needs to be set since state_id and
          state_path can be obtained.
          state_id:
            state_name:
              __alias__: None|<path>

        '''
        if not index:
            index = {}
        if not data:
            data = {}
        enabled = [str, {str: str}]
        schema = {
            Required('auto', default=False): Any(Coerce(bool)),
            Required('disabled', default=[]): Any([str], cls.coerce_to_list(str)),
            Required('enabled', default=[]): Any(enabled, cls.coerce_to_list(str)),
            Required('aliases', default=[]): [{str: Any(str, None)}],
        }
        # Repack short dictionary list as a dictionary
        data = cls.schema(data, schema, index)
        data['aliases'] = salt.utils.repack_dictlist(data['aliases'])
        return data


class RenderError(SaltRenderError):
    '''
    Used when the YamlScript renderer needs to raise an explicit error. If an
    index object are passed, get_context will be invoked to get the location
    of the error.
    '''
    header = '-- ERROR IN YAMLSCRIPT TEMPLATE ------------------'
    header2 = '-- DEBUGGING TRACE INFO --------------------------'
    _marker = object
    debug = True

    def __init__(self,
                 error,
                 value=_marker,
                 index=None,
                 mode=None):

        line_num = None
        buf = ''
        marker = '    <======================'
        trace = None

        if mode == 'exec':
            error, line_num, buf = self.exec_error(error, value, index)
        elif index:
            error, line_num, buf = self.index_error(error, value, index)
        else:
            error = self.basic_error(error, value)

        if line_num is not None:
            marker = '    <======[LINE {0}]======'.format(line_num)

        SaltRenderError.__init__(self, error, line_num, buf, marker, trace)

    @classmethod
    def exec_error(cls, error, value, index):
        msg, line_num, buf = cls.index_error(error, value, index)
        if isinstance(error, exceptions.SyntaxError):
            lineno = error[1][1]
        elif isinstance(sys.exc_info()[1], exceptions.SyntaxError):
            lineno = sys.exc_info()[1][1][1]
        else:
            lineno = 0
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname, lineno, fn_, text = frame  # pylint: disable=W0612

        line_num = lineno + index['key_start_line'] + 1 + index.get('key_start_line_offset', 0)
        return msg, line_num, buf

    @classmethod
    def index_error(cls, error, value, index):
        line_num = None
        if value is None:
            value = 'None|null'

        node_name = index['key']
        template = index['template']
        sls = index['sls']
        start = index.get('key_start_index', 0)
        start_line = index.get('key_start_line', 0)
        end = index.get('value_end_index', len(template))
        snippet = template[start:end]

        # XXX: why only splice [0]?
        if isinstance(value, list):
            value = value[0]

        # TODO: pattern may still need some work
        pdict = {
            'prefix': '' if not node_name.startswith('$') else '\$',
            'node_name': node_name if not node_name.startswith('$') else node_name[1:],
            'value_or_eol': '\\b{0}'.format(value) if value != cls._marker else '$',
        }
        pattern = r'({0[prefix]}\b{0[node_name]}).+?({0[value_or_eol]})'.format(pdict)

        # Ignore case to be able to match True/true, False/false
        pattern = re.compile(pattern, re.MULTILINE | re.DOTALL | re.IGNORECASE)

        for match in re.finditer(pattern, snippet):
            line_num = snippet.count("\n", 0, match.end()) + 1
            break

        if line_num:
            line_num = line_num + start_line

        msg = cls.text_trace()
        msg += '\n{0}\n{1}{2}\n{3}{4}\n{5}{6}{7}{8}{9}\n'.format(
            cls.header,
            'SLS FILE: ',
            sls or 'UNKNOWN',
            'NODE    : ',
            node_name,
            'VALUE   : ' if value != cls._marker else '',
            value if value != cls._marker else '',
            '\n' if value != cls._marker else '',
            'ERROR   : ',
            error,
        )
        return msg, line_num, template

    @classmethod
    def basic_error(cls, error, value):
        header = '{0}\n-- NO POSITIONAL INFO AVAILABLE --'.format(cls.header)
        msg = cls.text_trace()
        msg += '\n{0}\n{1}{2}{3}{4}{5}\n'.format(
            header,
            'value: ' if value != cls._marker else '',
            value if value != cls._marker else '',
            '\n' if value != cls._marker else '',
            'description of error: ',
            error,
        )
        return msg

    @classmethod
    def text_trace(cls):
        if not cls.debug:
            return ''

        try:
            fname, lineno, fn_, text = traceback.extract_tb(sys.exc_info()[2])[0]
        except IndexError:
            return ''

        msg = '\n{0}\n{1}{2}\n{3}{4}\n{5}{6}\n{7}{8}\n'.format(
            cls.header2,
            'FILENAME:  ',
            fname,
            'LINE NUM:  ',
            lineno,
            'FUNCTION:  ',
            fn_,
            'LINE TEXT: ',
            text
            )
        return msg


class YSOrderedDict(salt.utils.odict.OrderedDict):
    '''
    Extend OrderedDict so we can store positional information for debugging
    '''
    __index__ = None

    def __init__(self, *args, **kwds):
        '''
        args[0]: Initialize with arg[0] dictionary
        args[1]: (list) - Contains a list of string names to include when
                          creating the dictionary so a listing containing
                          ['users']['user']['file'] would only copy the 'tree'
                          values from arg[0] leaving a dictionary with the
                          following structure:
                          {user: {user: {file: <everything under file>}}}
        args[1]: (YSOrderedDict) - will be used only to set the __index__
                          parameters
        '''
        self.__index__ = {}

        if len(args) > 2:
            raise TypeError('expected at most 2 arguments, got %d' % len(args))
        elif len(args) == 2 and not (isinstance(args[1], list) or isinstance(args[1], YSOrderedDict)):
            raise TypeError('expected a list or YSOrderedDict as second argument, got %d' % type(args[1]))
        super(YSOrderedDict, self).__init__()

        # create dictionary from sections provided
        # skips **kwds
        if len(args) == 2 and isinstance(args[1], list):
            if not args[1]:
                self.update(args[0], **kwds)
                return
            other = args[0]
            sections = args[1]

            for i, section in enumerate(sections):
                info = other.__index__.get(section, {}) if isinstance(other, YSOrderedDict) else {}
                other = other[section]
                if i == len(sections) - 1:
                    self.setdefault(sections[i], other)
                    self.__index__[sections[i]] = info
                else:
                    self.setdefault(sections[i], YSOrderedDict())
                    self.__index__[sections[i]] = info
                    self = self[section]
        else:
            self.update(*args, **kwds)

    def update(self, *args, **kwds):
        if args:
            super(YSOrderedDict, self).update(args[0], **kwds)
        else:
            super(YSOrderedDict, self).update(**kwds)

        if len(args) == 1 and isinstance(args[0], YSOrderedDict):
            for key in args[0].__index__.keys():
                self.__index__[key] = args[0].__index__[key]
        elif len(args) == 2 and isinstance(args[1], YSOrderedDict):
            for key in self.keys():
                if key in args[1].__index__.keys():
                    self.__index__[key] = args[1].__index__[key]

    def setdefault(self, key, default=None, info=None):  # pylint: disable=W0221
        if info:
            if isinstance(info, YSOrderedDict) and key in info.__index__.keys():
                self.__index__[key] = info.__index__[key]
        return super(YSOrderedDict, self).setdefault(key, default)

    def update_at(self, other, index=0):
        'updates the dictionary at index position'
        if hasattr(other, 'viewitems'):
            other = other.viewitems()
        ins = [(k if k not in self else self[k], v) for k, v in other]
        if ins:
            left = self.items()[0:index]
            right = self.items()[index:]
            self.clear()
            self.update(left)
            self.update(ins)
            self.update(right)

    def insert(self, item, index=0):
        'insert a single item at index position'
        replace = self.items()
        replace.insert(index, item)
        self.clear()
        self.update(replace)

    def insert_before(self, key, item):
        'insert a single item before key name'
        self.insert(self.keys().index(key), item)

    def insert_after(self, key, item):
        'insert a single item after key name'
        self.insert(self.keys().index(key) + 1, item)

    def rename(self, key, new_key):
        'rename a key.  keeps position in ordereddict'
        replace = [(new_key if k == key else k, v) for k, v in self.iteritems()]
        self.clear()
        self.update(replace)
        if key in self.__index__.keys():
            self.__index__[new_key] = self.__index__.pop(key)

    @classmethod
    def convert(cls, dict_):
        'converts any dictionary and nested dictionaries to a YSOrderedDict'
        for key, value in dict_.iteritems():
            if isinstance(value, collections.Mapping) and not isinstance(value, YSOrderedDict):
                dict_[key] = cls.convert(dict_[key])
            elif isinstance(value, list):
                for element in value:
                    if isinstance(element, collections.Mapping) and not isinstance(element, YSOrderedDict):
                        value[value.index(element)] = cls.convert(element)
        return YSOrderedDict(dict_)


class YamlScriptSafeLoader(SaltYamlSafeLoader, object):
    '''
    create a custom YAML loader that uses the custom constructor.

    The default salt loader will not allow duplicate key, which can exist
    within yamlscript for yamlscript $commands so those keys are caught and
    renamed by appending '# <position>' where <position> is len(mapping).
    '''
    BAD_CHARS = {'none': None, 'true': True, 'false': False}
    sls = ''
    template = ''

    def convert_bad_chars(self, value):
        '''
        yaml pillar conversion can convert values such as None to a string and we don't
        want that, so we fix it here
        '''
        if isinstance(value, str):
            if value.strip().lower() in self.BAD_CHARS:
                return self.BAD_CHARS[value.strip().lower()]
        return value

    def __init__(self, stream, dictclass=YSOrderedDict):
        self.template = stream
        salt.utils.yamlloader.SaltYamlSafeLoader.__init__(self, stream, dictclass)

    def construct_mapping(self, node, deep=False):
        '''
        Build the mapping for YAML
        '''
        if not isinstance(node, salt.utils.yamlloader.MappingNode):
            raise salt.utils.yamlloader.ConstructorError(
                None,
                None,
                'expected a mapping node, but found {0}'.format(node.id),
                node.start_mark)

        self.flatten_mapping(node)

        mapping = self.dictclass()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hash(key)
            except TypeError:
                err = ('While constructing a mapping {0} found unacceptable '
                       'key {1}').format(node.start_mark, key_node.start_mark)
                raise salt.utils.yamlloader.ConstructorError(err)
            value = self.construct_object(value_node, deep=deep)
            value = self.convert_bad_chars(value)
            if key in mapping:
                if is_script_node(key):
                    key = ''.join('{0} #{1}'.format(key, len(mapping)))
                # We want to know about it if key is still not unique enough
                if key in mapping:
                    raise salt.utils.yamlloader.ConstructorError('Conflicting ID "{0}"'.format(key))

            # Store positional information for debugging
            index = {'key': key,
                     'key_start_line': key_node.start_mark.line,
                     'key_start_index': key_node.start_mark.index,
                     'key_end_line': key_node.end_mark.line,
                     'key_end_index': key_node.end_mark.index,
                     'value_start_line': value_node.start_mark.line,
                     'value_start_index': value_node.start_mark.index,
                     'value_end_line': value_node.end_mark.line,
                     'value_end_index': value_node.end_mark.index,
                     'sls': self.sls,
                     'template': self.template,
                     }
            mapping.__index__[key] = index  # pylint: disable=E1103
            mapping[key] = value
        return mapping


def debug(*args):
    '''
    Pretty print debug messages if debugging enabled
    '''
    # So we can debug our output if needed
    _debug = False
    if _debug:
        print 'debug(): type({0})'.format(type(args))

    if isinstance(args, tuple) and len(args) == 1:
        args = args[0]

    if _debug:
        print 'debug(): type({0})'.format(type(args))

    if isinstance(args, DataWrapper):
        args = args._data  # pylint: disable=E1103, W0212

    if isinstance(args, salt.utils.odict.OrderedDict):
        if _debug:
            print 'debug(): Format as OrderedDict (json)'
        print json.dumps(args, indent=2)
    elif isinstance(args, dict) or isinstance(args, list):
        if _debug:
            print 'debug(): Format as dict (pprint)'
        pprint.pprint(args)
    else:
        if _debug:
            print 'debug(): Format as plain (print)'
        print args


class DataWrapper(object):
    '''
    Wrap an existing dict, or create a new one, and access with either dot
    notation or key lookup.

    The attribute _data is reserved and stores the underlying dictionary.
    When using the += operator with default=True, the empty nested dict is
    replaced with the operand, effectively creating a default dictionary
    of mixed types.

    d({})
        Existing dict to wrap, an empty dict is created by default

    default({})
        Create an e default value instead of raising a KeyError

    example:
      >>>dw = DataWrapper({'pp':3})
      >>>dw.a.b += 2
      >>>dw.a.b += 2
      >>>dw.a['c'] += 'Hello'
      >>>dw.a['c'] += ' World'
      >>>dw.a.d
      >>>print dw._data
      {'a': {'c': 'Hello World', 'b': 4, 'd': {}}, 'pp': 3}

    '''
    __marker = object()

    def __init__(self, d=None, default=__marker):
        if not d:
            d = {}
        supr = super(DataWrapper, self)
        supr.__setattr__('_data', d)
        supr.__setattr__('__default', default)
        supr.__setattr__('__empty', self.__Empty__())

    def __getattr__(self, name):
        try:
            value = self._data[name]
        except KeyError:
            if not super(DataWrapper, self).__getattribute__('__default'):
                value = super(DataWrapper, self).__getattribute__('__default')
                self._data[name] = value
            elif super(DataWrapper, self).__getattribute__('__default') == self.__marker:
                return super(DataWrapper, self).__getattribute__('__empty')
            else:
                raise

        # If value is a dictionary; wrap it
        if hasattr(value, 'items'):
            default = super(DataWrapper, self).__getattribute__('__default')
            return DataWrapper(value, default=default)
        return value

    def __setattr__(self, name, value):
        self._data[name] = value

    def __getitem__(self, key):
        try:
            value = self._data[key]
        except KeyError:
            if not super(DataWrapper, self).__getattribute__('__default'):
                value = super(DataWrapper, self).__getattribute__('__default')
                self._data[key] = value
            elif super(DataWrapper, self).__getattribute__('__default') == self.__marker:
                return super(DataWrapper, self).__getattribute__('__empty')
            else:
                raise

        # If value is a dictionary; wrap it
        if hasattr(value, 'items'):
            default = super(DataWrapper, self).__getattribute__('__default')
            return DataWrapper(value, default=default)
        return value

    def __setitem__(self, key, value):
        self._data[key] = value

    def __iadd__(self, other):
        if self._data:
            raise TypeError("A Nested dict will only be replaced if it's empty")
        else:
            return other

    def __str__(self):
        return self._data.__str__()

    def __repr__(self):
        return self._data.__repr__()

    @staticmethod
    class __Empty__(object):
        # pylint: disable=C0103
        def __len__(self):
            return 0

        def __getitem__(self, key):
            return self

        def __getattr__(self, key):
            return self

        def __call__(self):
            return (None, None)

        def get(self, key, failobj=None):  # pylint: disable=W0613
            return self

        def __contains__(self, key):
            return self

        def __str__(self):
            return 'EMPTY - NoneType'

        def __repr__(self, _repr_running=None):
            return 'EMPTY - NoneType'


def update(target, source, create=False, allowed=None):
    '''
    Updates the values of a nested dictionary of varying depth without over-
    writing the targets root nodes.

    Original code example from:
    http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth

    target
        Target dictionary to update

    source
        Source dictionary that will be used to update `target`

    create
        if True then new keys can be created during update, otherwise they will be tossed
        if they do not exist in `target`.

    allowed
        list of allowed keys that can be created even if create is False
    '''
    if not allowed:
        allowed = []

    for key, value in source.items():
        if isinstance(value, collections.Mapping):
            if key in target.keys() or create or key in allowed:
                replace = update(target.get(key, {}), value, create=create)
                target[key] = replace
        else:
            if key in target.keys() or create or key in allowed:
                target[key] = source[key]
    return target


def is_script_node(key):
    '''
    Returns the token stripped of the leading '$' and spaces if found
    Returns None if key starts with a '$' but is not valid
    Returns False otherwise
    '''
    valid_keys = ['$python', '$for ', '$if ', '$elif ', '$else', '$with', '$include', '$extend', '$pillars',
                  '$test_file', '$defaults', '$comment', '$import']
    for k in valid_keys:
        if key.startswith(k):
            return k.strip()[1:]
    if key.startswith('$'):
        return None
    return False


_marker = object


def set_alias(data, pillars, state_id, state_name):
    '''
    If a pillar exists, it will set as __pillar_data__ and returned.
    Aliases can be used to assist locatinf the pillar

    This Allows shorter path names to values when looking up pillar values.

    set_aliases does not check if pillar_data should be used or not; that
    is up to the calling function to provide those checks (set_pillar does)
    '''
    pillar = data.get('__pillar__', state_id)
    pillar_data = data.get('__pillar_data__', {})
    if pillar is not False and not pillar_data:
        pillar_data = __pillar__.get(pillar, {})

    # Over-ride pillar preferences and allow since no checks are done here
    if pillar is False:
        pillar = state_id

    alias = data.get('__alias__', _marker)
    if alias == _marker:
        if state_name:
            pillar = '{0}.{1}'.format(pillar, state_name)

        alias = pillars['aliases'].get(pillar, _marker)

        # alias not found; automatically see if we can find one
        if alias == _marker:
            # pillar is not nested; use found pillar
            # pillar_id.state_name key
            if pillar_data.get(pillar, _marker) != _marker:
                alias = pillar

            # state_name key
            elif state_name and pillar_data.get(state_name, _marker) != _marker:
                alias = state_name

            else:
                # Just can't find a suitable match to be able to provide
                # pillar data in a reliable manner
                alias = False

        data['__alias__'] = alias

    # If the pillar_key is set to null/None we want the root
    if alias is False:
        pillar_data = {}
    elif alias is not None:
        pillar_data = pillar_data.get(alias, {})
    data['__pillar_data__'] = pillar_data

    # XXX: Template
    return pillar_data


def set_pillar_data(data, pillars, state_id, state_name):
    '''
    Don't allow pillar merging for templates that are not yamlscript
    since UNLESS the __pillar__ key has already been set or
    pillars.auto has been set to 'all'

    Any yamlscript that has already been generated will already have a
    __pillar__ declaration, so we wont need to worry about rules set within
    '''

    def is_true(key):
        for value in pillars[key]:
            if isinstance(value, str) and state_id == value:
                return True
            elif isinstance(value, dict) and state_id in value.keys():
                return value[state_id]  # Will need the mapped value
        return False

    pillar = data.get('__pillar__', None)
    if pillar is False:
        return {}
    elif pillar:
        return set_alias(data, pillars, state_id, state_name)

    # Check to see if we should even search for pillar data
    auto = pillars['auto']
    disabled = is_true('disabled')
    enabled = is_true('enabled')

    if auto and disabled:
        pillar = False
    elif not auto and enabled:
        pillar = enabled
    # XXX: Added for Template
    elif auto:
        pillar = state_id
    else:
        pillar = False

    data['__pillar__'] = pillar
    if pillar is False:
        return {}

    return set_alias(data, pillars, state_id, state_name)


def compile_state_data(
        data,
        state_id=None,
        state_name=None,
        set_defaults=False,
        attach_defaults=False,
        pillars=None):
    '''
    Takes salt structured data like {id}{state[.function]}[{function value list}]
    and converts it to {id}{state}{key:values}

    Returns an YSOrderedDict ordered dictionary
    '''
    if state_name is not None and '.' in state_name:
        state_name = state_name.split('.')[0]

    # Lets not mess with original
    if state_id is not None:
        if state_id not in data.keys():
            raise KeyError
        data = copy.deepcopy(YSOrderedDict(data, [state_id]))
    else:
        data = copy.deepcopy(YSOrderedDict(data))

    valid_keys = [
        'name',
        'names',
        '__id__',
        '__fun__',
        '__argspec__',
        '__pillar__',
        '__alias__',
        '__pillar_data__'
    ]

    # be sure all the data is YSOrderedDict type
    data = YSOrderedDict.convert(data)
    high = YSOrderedDict()

    # Split apart any state.function combinations
    for state_id, states in data.items():
        for key in states:
            if not isinstance(states[key], list):
                continue
            if '.' in key:
                comps = key.split('.')
                states.rename(key, comps[0])
                states[comps[0]].append(comps[1])
                key = comps[0]
            if state_name is not None and state_name != key:
                continue

            high.setdefault(state_id, YSOrderedDict(), data)
            high[state_id].setdefault(key, YSOrderedDict(), states)

            # Find function and add it as __fun__:
            for value in states[key]:
                if isinstance(value, str):
                    high[state_id][key]['__fun__'] = value
                elif isinstance(value, dict):
                    high[state_id][key].update(value)
                else:
                    continue

            state_values = high[state_id][key]
            state_func_name = '{0}.{1}'.format(key, state_values['__fun__'])

            if set_defaults or attach_defaults:
                function = __states__[state_func_name]
                args, kwargs = salt.utils.arg_lookup(function).values()

                if set_defaults:
                    for k in args:
                        state_values.setdefault(k, None)

                    for k, val in kwargs.items():
                        state_values.setdefault(k, val)

                if attach_defaults:
                    valid_keys.extend(args)
                    valid_keys.extend(kwargs.keys())
                    state_values['__argspec__'] = valid_keys
                    set_pillar_data(state_values, pillars, state_id, state_name)
    return high


class Deserialize(object):
    test_data = YSOrderedDict()
    script_data = YSOrderedDict()
    templates = YSOrderedDict()
    state_list = []
    pillars = {}
    script_node = None
    index = None

    def __init__(self, template, saltenv='base', sls='', defaults=False, **kwargs):
        self.template = template
        self.saltenv = saltenv
        self.sls = sls
        self.sls_type = kwargs.get('sls_type', None)
        self.kwargs = kwargs
        self.client = salt.fileclient.get_file_client(__opts__)

        self.defaults = defaults

        if isinstance(template, dict):
            self.state_file_content = YSOrderedDict.convert(template)
            self.pillars = Schema.pillars()
            self.pillars['auto'] = False
        else:
            # Set sls name in YamlScriptSafeLoader so it can be included when
            # creating __index__
            self.pillars = Schema.pillars()
            template.seek(0)
            self.template = template.read()
            template.seek(0)
            YamlScriptSafeLoader.template = self.template
            YamlScriptSafeLoader.sls = self.sls
            self.state_file_content = self.deserialize_yamlscript_file(template)

    def get_state_dest(self, sls):
        state_data = self.client.get_state(sls, self.saltenv)
        dest = state_data.get('dest', False)
        if not dest:
            raise RenderError('No such file or directory', sls, index=self.index)
        return dest

    def get_state_source(self, sls):
        state_data = self.client.get_state(sls, self.saltenv)
        source = state_data.get('source', False)
        if not source:
            raise RenderError('No such file or directory', sls, index=self.index)
        return source

    def get_salt_file(self, salt_file):
        try:
            state_file = self.client.cache_file(salt_file, self.saltenv)
            with open(state_file) as file_:
                return file_.read()
        except IOError, error:
            raise RenderError(error, salt_file, self.index)

    @staticmethod
    def deserialize_yamlscript_file(template):
        template.seek(0)
        return salt.utils.serializers.yaml.deserialize(template.read(), **{'Loader': YamlScriptSafeLoader})

    def deserialize_salt_file(self, template):
        return salt.utils.serializers.yaml.deserialize(self.get_salt_file(template))

    def deserialize_salt_files(self, templates):
        state_file_content = []
        if isinstance(templates, str):
            templates = [templates]
        for data in templates:
            data = self.deserialize_salt_file(data)
            state_file_content.append(data)
        return state_file_content

    def generate(self, state_file_content, script_data):
        '''
        '''
        for key_node, value_node in state_file_content.items():
            # Make positional debugging info available
            if hasattr(state_file_content, '__index__'):
                self.index = state_file_content.__index__.get(key_node, {})
            else:
                self.index = {}

            # script_node returns None if it had a '$' prefix, but invalid token
            script_node = is_script_node(key_node)
            if script_node is None:
                raise RenderError('Invalid Yamlscript token', index=self.index)

            if script_node:
                self.script_node = script_node
                key_node = key_node[1:]  # Strip '$' token
                command = YSOrderedDict(
                    {'__yamlscript__':
                     {'type': script_node,
                      'statement': ''.join(key_node.split("#")[0]).strip(),
                      'index': self.index
                      }
                     }
                )

                # $defaults
                if script_node == 'defaults':
                    self.defaults = value_node

                # $python
                elif script_node in ['python']:
                    command['__yamlscript__']['statement'] = value_node
                    script_data[key_node] = command
                    script_data.__index__['$' + key_node] = self.index

                # $pillar
                elif script_node == 'pillars':
                    self.pillars = Schema.pillars(value_node, self.index)

                # $test_file
                elif script_node == 'test_file':
                    for data in self.deserialize_salt_files(value_node):
                        data = data.get('local', data)
                        self.test_data.update(data)

                # $with
                elif script_node == 'with' and isinstance(value_node.values()[0], list):
                    # 'with' node withing YAML syntax only
                    id_ = key_node.split(' ', 1)[1]
                    new_key_node = YSOrderedDict({id_: YSOrderedDict()})
                    new_key_node.__index__[id_] = state_file_content.__index__['$' + key_node]
                    new_key_node[id_].update(YSOrderedDict({value_node.keys()[0]: value_node.values()[0]}, value_node))

                    # Just leave the nested items in value_node so we can attach them later
                    value_node.pop(value_node.keys()[0])

                    # create command object, then attach the nested content
                    script_data[key_node] = self.generate(new_key_node, command)
                    content = self.generate(value_node, YSOrderedDict())
                    script_data[key_node]['__yamlscript__']['content'] = content
                    script_data.__index__['$' + key_node] = self.index

                # $import
                elif script_node == 'import':
                    if isinstance(value_node, str):
                        value_node = [value_node]
                    for sls in value_node:
                        source = self.get_state_source(sls)
                        data = self.generate(
                                self.deserialize_yamlscript_file(StringIO.StringIO(self.get_salt_file(source))),
                                YSOrderedDict()
                            )

                        # Don't allow duplicate keys or values could be over-written
                        for key_data, value_data in data.items():
                            if '$' + key_data in state_file_content.keys():
                                key_data += source
                            script_data[key_data] = value_data

                # $include
                elif script_node == 'include':
                    if isinstance(value_node, str):
                        value_node = [value_node]
                    for sls in value_node:
                        dest = self.get_state_dest(sls)
                        try:
                            kwargs = copy.deepcopy(self.kwargs)
                            state = salt.template.compile_template(dest,
                                                                   renderers=kwargs.pop('renderers'),
                                                                   default=__opts__['renderer'],
                                                                   saltenv=self.saltenv,
                                                                   sls=sls,
                                                                   **kwargs
                                                                   )
                        except SaltRenderError:
                            raise

                        # If a yamlscript sls file was included, it cached the
                        # Deserialize instance, so we use it
                        if isinstance(Cache.get(sls), Deserialize):
                            deserialize = Cache.get(sls)
                            self.test_data.update(deserialize.test_data)
                            Cache.pop(sls)
                        else:
                            deserialize = Deserialize(state,
                                                      saltenv=self.saltenv,
                                                      sls=sls,
                                                      **self.kwargs
                                                      )
                            deserialize.generate(deserialize.state_file_content, YSOrderedDict())
                        script_data.update(deserialize.script_data)
                        self.state_list.extend(deserialize.state_list)

                # $for, $if, $elif, $else, $with
                elif script_node in ['for', 'if', 'elif', 'else', 'with']:
                    script_data[key_node] = self.generate(value_node, command)
                    script_data.__index__['$' + key_node] = self.index

                # $comment
                elif script_node in ['comment']:
                    pass

                else:
                    raise RenderError('Yamlscript token not implemented', value_node, index=self.index)
                continue

            # sls '- include' - convert to a yamlscript $include and parse it
            elif key_node == 'include':
                state_file_content.rename(key_node, '${0}'.format(key_node))
                key_node = '${0}'.format(key_node)
                self.generate(YSOrderedDict(state_file_content, [key_node]), script_data)
                continue

            # Deal with pillars
            if self.sls_type == 'pillar':
                # TODO:  No positional info available!
                script_data.setdefault(key_node, YSOrderedDict(), state_file_content)
                script_data[key_node].update(YSOrderedDict(pillar=value_node))
                continue

            # Deal with templates
            elif self.sls_type == 'template':
                script_data.setdefault(key_node, YSOrderedDict(), state_file_content)
                script_data[key_node].update(YSOrderedDict(template=value_node))

                # Set alias to None if not already set to ensure pillar data can be found
                if self.pillars['aliases'].get(key_node, None) is None:
                    self.pillars['aliases'][key_node + '.template'] = None

                # Retreive any related pillar data for template
                pd = set_pillar_data(script_data[key_node], self.pillars, key_node, 'template')

                # Replace data with pillar data
                if pd:
                    script_data[key_node]['template'] = pd

                self.state_list.append((key_node, 'template'))  # XXX: Is this needed
                continue

            # Only deal with one item at a time
            elif isinstance(value_node, dict) and len(value_node) > 1:
                for nested_script_data in value_node.keys():  # pylint: disable=E1103
                    if is_script_node(nested_script_data):
                        self.generate(
                            YSOrderedDict(
                                {nested_script_data: YSOrderedDict(
                                    {key_node: state_file_content[key_node][nested_script_data]},
                                    state_file_content
                                )
                                }, state_file_content[key_node]
                            ), script_data
                        )
                        # XXX: Why break?  we not completeing other nested data
                        ### break
                    else:
                        self.generate(YSOrderedDict(state_file_content, [key_node, nested_script_data]), script_data)
                continue

            # Allow empty states like cmd.run
            elif isinstance(value_node, str):
                value_node = YSOrderedDict({value_node: []})
                state_file_content[key_node] = value_node

            elif not isinstance(value_node, dict):
                raise RenderError('Not implemented', index=self.index)

            state_name = value_node.keys()[0]  # pylint: disable=E1103
            if '.' in state_name:
                state_name = state_name.split('.')[0]

            high = compile_state_data(
                YSOrderedDict(state_file_content, [key_node]),
                state_id=key_node,
                state_name=state_name,
                set_defaults=self.defaults,
                attach_defaults=True,
                pillars=self.pillars
            )
            script_data.setdefault(key_node, YSOrderedDict(), state_file_content)
            script_data[key_node].update(YSOrderedDict(high[key_node], [state_name]))
            self.state_list.append((key_node, state_name))

        self.script_data = script_data
        return script_data


class Cache(object):
    '''
    Cache is used to cache copies of Deserialize instances when
    an 'include' statement is provided in the template since we will want to
    be able to use the already rendered data if available for tests and not
    have to deserialize the script data again.
    '''
    cache = {}

    @classmethod
    def __init__(cls, context):
        'context is a global varable used to hold the cache'
        if 'yamlscript_cache' not in context.keys():
            context['yamlscript_cache'] = {}
        cls.cache = context['yamlscript_cache']

    @classmethod
    def all(cls):
        'returns the complete cache dictionary'
        return cls.cache

    @classmethod
    def get(cls, sls):
        'get a cached item from cache'
        return cls.cache.get(sls, None)

    @classmethod
    def set(cls, sls, value):
        'set an item to be cached'
        cls.cache[sls] = value

    @classmethod
    def pop(cls, sls):
        'remove an item from the cache'
        cls.cache.pop(sls, None)


def test(salt_data, test_data, sls=''):
    '''
    Runs a test to confirm state values provided in test file matched the
    generated salt_data values exactly as well as confirming the id's of
    the yaml represented states.

    :param OrderedDict salt_data: pyobjects generated state data
    :param YSOrderedDict test_data: De-serialized test data
    :return: number of errors in test1 and test2
    :rtype: int, int

    The best way to run tests is to call the state you are running directly
    like:
    `salt-call --local --out=yaml state.show_sls users`

    test_data can be included in the state file and defined as a list like:

    .. code-block:: yaml

        $test_file:
          - salt://users/tests.mel
          - salt://users/tests.bobby

    And the test_data file should look something like this:

    .. code-block:: yaml

        local:
          mel_shadow_group:
            group:
            - addusers: null
            - delusers: null
            - gid: null
            - members: null
            - name: shadow
            - system: false
            - present
          mel_sudo_group:
          ...

    The test runs two ways, first confirming all expected salt_data is with
    test_data, then the other way around testing if there are extra values
    within the salt_data that are not in the test_data.
    '''
    # Ignore these keys since they may differ on each run
    ignore = ['order', '__sls__', '__env__']

    # Compile salt_data into a valid yamlscript structure
    salt_data = compile_state_data(salt_data)

    # Deserialize test state file
    if isinstance(test_data, str):
        test_data = salt.utils.serializers.yaml.deserialize(test_data)

    # Compile test_data into a valid yamlscript structure and allow test_data to
    # contain the parent 'local' key as shown 'state.show_sls users' or not
    test_data = compile_state_data(test_data.get('local', test_data))

    def compare(test_data, data, text=None, mismatch='mismatch', key_error='key_error'):
        '''
        Function that compares test_data to salt_data and generates a list of
        errors that will be displayed

        :param YSOrderedDict test_data: used as the base to test from
        :param YSOrderedDict data: data is compared to see if it matches test_data
        :param dict text: dictionary of all default text messages to use
        :param str mismatch: key to use to identify a data mismatch that refers to a message in text
        :param str key_error: key to use to identify a data key_error that refers to a message in text
        :return: a list of error messages
        :rtype: list
        '''
        if not text:
            text = {}
        errors = []
        for state_id, states in test_data.items():
            for state_name, state_values in states.items():
                for key, value in state_values.items():
                    if key in ignore:
                        continue
                    try:
                        result_vars = dict(state_id=state_id,
                                           state_name=state_name,
                                           key=key,
                                           value=value)
                        data_value = data[state_id][state_name][key]
                        result_vars.update(data_value=data_value)
                        if value != data_value:
                            # MISMATCH
                            if result_vars['value'] == '':
                                result_vars['value'] = "\'\'"
                            if result_vars['data_value'] == '':
                                result_vars['data_value'] = "\'\'"
                            errors.append(text[mismatch].format(result_vars))
                    except KeyError:
                        # KEY ERROR
                        if result_vars['value'] == '':
                            result_vars['value'] = "\'\'"
                        errors.append(text[key_error].format(result_vars))
        return errors

    sls = ' ({0})'.format(sls) if sls else sls
    text = {
        'mismatch': '<> MISMATCH: {{{0[state_id]}}}:{{{0[state_name]}}}:{{{0[key]}}} is {0[data_value]} but should '
                    'be: {0[value]}',
        'key_error': '-- MISSING : {{{0[state_id]}}}:{{{0[state_name]}}} does not contain key {{{0[key]}: {0[value]}}}',
        'key_error2': '++ EXTRA   : {{{0[state_id]}}}:{{{0[state_name]}}}:{{{0[key]}: {0[value]}}} not in test_data',
        'test_data': 'TEST RESULTS - THE FOLLOWING IS MISSING FROM RENDERED STATE FILE',
        'ruler': '========================================================================================',
        'salt_data': 'TEST RESULTS - THE FOLLOWING IS PRESENT IN GENERATED STATE FILE, BUT NOT IN TEST FILE',
        'end': 'TEST RESULTS - END =====================================================================',
        'blank': '', 'no_error_test': 'Yamlscript Renderer{0}: No errors for test_data'.format(sls),
        'no_error_salt': 'Yamlscript Renderer{0}: No errors for salt_data'.format(sls)
    }

    test1 = compare(test_data, salt_data, text=text)
    if test1:
        print text['test_data']
        print text['ruler']
        for message in test1:
            print message
        print text['blank']
    else:
        print text['no_error_test']

    test2 = compare(salt_data, test_data, text=text, mismatch='', key_error='key_error2')
    if test2:
        print text['salt_data']
        print text['ruler']
        for message in test2:
            print message
        print text['blank']
    else:
        print text['no_error_salt']

    return len(test1), len(test2)
