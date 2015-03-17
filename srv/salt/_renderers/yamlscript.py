# -*- coding: utf-8 -*-
#
# DockerNAS - User Salt State Formulas - Version 0.0.1
# Copyright 2014 Jason Mehring
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
##############################################################################

'''
DOCS - Overview of Features:
----------------------------
- Combine python and yaml in a nice human readable yaml format.  All the
  power of python with readability of YAML
- Can automatically get pillar data and inject into state
- Non yaml state files such as yaml, jinga, and pyobjects can be included.
  Those state files will be injected into the yamlscript template
  where their values can be read or even modified.  And pre-processing
  on the state files, such a jinga2 templating will automatically take
  place in advance.  It can be as easy as just adding pillar data and run
  with no state file modifications except adding the !#yamlscript shebang (or
  appending it to an existing one)
- Access to read / write to any state file value
- requisites are automatically calculated just by using with: statement
  and nesting (indenting) underneath
- test mode available to test state files against a test file before deployment
- support for pyobjects maps; yaml format available for creating them
- tracking of error positions in python snippets that will display real line number
  error is one in state file compare to a generic stack trace related to
  yamlscript source files

Cavaets:
--------
- You must escape any scalar value that begins with a '$' with another
  '$' so to produce '$4.19', escape like this: '$$4.19'

'''

# pylint: disable=W0511
# ---------------------
# W0511: TODO
# W0511: XXX

# pylint: disable=W0212
# ---------------------
# W0212: Access to a protected member _data of a client class
# W0212: Access to a protected member _locals of a client class
# W0212: Access to a protected member _script_data of a client class


import sys
import re
import StringIO
import copy

import salt.loader
import salt.fileclient
from salt.utils.pyobjects import Registry

import yamlscript_utils
from yamlscript_utils import (RenderError,
                              DataWrapper,
                              YSOrderedDict,
                              update,
                              ###get_pillar_data,
                              debug
                              )


try:
    __context__['yamlscript_loaded'] = True
except NameError:
    __context__ = {}


def get_state_function(state_name, function):
    '''
    Return the pyobjects state module factory function

    :param str state_name: State name key in `[state_id][state_name]`
    :return: pyobjects factory state function
    '''

    state_camel = ''.join([
        part.capitalize()
        for part in state_name.split('_')
    ])
    module = globals().get(state_camel, None)
    state_function = getattr(module, function, None)
    return state_function

def find_state(data, state_id, state_name, replace=None):
    '''
    State could be nested somewhere in the defaults dictionary so keep looking
    until its found

    TODO:  Add some type of caching since this function can be quite expensive
    '''
    if replace and isinstance(replace, DataWrapper):
        replace = replace._data  # pylint: disable=W0212

    if isinstance(data, DataWrapper):
        data = data._data  # pylint: disable=W0212

    if not isinstance(data, dict):
        return None

    # If state is in root node, return it
    if (state_id in data.keys()
            and isinstance(data[state_id], dict)
            and state_name in data[state_id].keys()):
        if replace:
            data[state_id][state_name] = replace[state_name]
        return data

    for key_node, value_node in data.items():
        if (isinstance(value_node, dict)
                and state_id in value_node.keys()
                and isinstance(value_node[state_id], dict)
                and state_name in value_node[state_id].keys()):
            if replace:
                data[key_node][state_id][state_name] = replace[state_name]
            return data[key_node]
        elif isinstance(value_node, dict):
            state = find_state(value_node, state_id, state_name)
            if state is not None:
                if replace:
                    state[state_id][state_name] = replace[state_name]
                return state

    # Could not find state
    return None


class Data(object):
    '''
    Data contains all the default state values as well as any generated states
    and exposes them though _locals which allow reading, modification and
    manipulation of the states via python or pilar data.

    Data also deals with merging and updating state values via pillars; either
    manually or automatically and updates directed from python code.  It will
    also reset values when scope changes at a command scripts request.
    '''
    _states = {}
    _state_list = []
    _locals = {}
    _script_data = {}

    def __init__(self, script_data):
        self._state_list.extend(copy.deepcopy(__context__['state_list']))
        self._script_data = script_data

        for state_id, state_name in self._state_list:
            self.add(self._script_data, state_id, state_name)

    def add(self, data, state_id, state_name, other_data=None):
        '''
        Adds a raw state to states so its values can be accessed by
        the yamlscript template.  These values are used to create
        the final state.

        :param YSOrderedDict data: De-serialized script_data (nested)
        :param str state_id: State id key in `data[state_id]`
        :param str state_name: State name key in `data[state_id][state_name]`
        :param dict other_data: Provided from template via python call
        :return: data value of [state_id][state_name]
        '''
        if not other_data:
            other_data = {}

        # Add the id/state to state_list if it does not already exist
        if (state_id, state_name) not in self._state_list:
            self._state_list.append((state_id, state_name))

        data = self.merge(data, state_id, state_name, other_data)
        if data is None:
            return None

        # Don't clobber
        self._states.setdefault(state_id, {}).setdefault(state_name, {})
        self._states[state_id][state_name] = data

        # Add state to _locals
        self._locals[state_id] = DataWrapper(self._states[state_id])

        return data

    def update(self, data, other_data=None):
        '''
        Find and valid state structures within data and update them to default

        :param YSOrderedDict data: De-serialized script_data (nested)
        :param dict other_data: Provided from template via python call
        :return: data value of [state_id][state_name]
        '''
        if not other_data:
            other_data = {}
        else:
            other_data['__create__'] = True

        # __context__['state_list'] contains all the ORIGINAL states; none
        # of the created ones will be updated since we don't want any values
        # changed of the already created states (__id__ would have change the
        # id)
        for state_id, state_name in __context__['state_list']:
            state = find_state(data, state_id, state_name)
            if state is None:
                continue
            self.add(data, state_id, state_name, other_data)
        other_data.pop('__create__', None)
        return data

    def merge(self, data, state_id, state_name, other_data=None):
        '''
        Merge pillar_data and/or other_data with state file defaults

        :param YSOrderedDict data: De-serialized script_data (nested)
        :param str state_id: State id key in `data[state_id]`
        :param str state_name: State name key in `data[state_id][state_name]`
        :param dict other_data: Provided from template via python call
        :return: data value of [state_id][state_name]
        '''
        pillar_data = {}
        if not other_data:
            other_data = {}

        create = other_data.get('__create__', False)

        # state_id may be currently out of scope in data if nested; lets check
        data = find_state(data, state_id, state_name)
        if data is None:
            data = find_state(self._states, state_id, state_name)

        # Could not find the state
        if data is None:
            return None

        data = data[state_id][state_name]

        # Only merge pillar_data if state_id does not already exist in
        # self._states so we don't clobber something thats been updated
        # already
        if state_id not in self._states:
            try:
                pillar_data = data.get('__pillar_data__', {})
            except AttributeError: pass

        # Allow other_data to honour aliases
        if other_data:
            other_data = self.other_aliases(data, state_id, state_name,
                                            other_data)

        # Only allow pillar data keys that exist in __argspec__ or in sls
        # template
        pillar_data = copy.deepcopy(pillar_data)
        update(pillar_data, other_data, create=True)

        # Nothing to merge
        if not pillar_data:
            return data

        if create:
            # Don't merge any keys not in __argspec__ OR state file.  Prevents
            # keys getting merged that share same pillar 'name space' when using
            # short aliases
            for key in pillar_data.keys():
                if key not in data['__argspec__'] and key not in data.keys():
                    pillar_data.pop(key, None)
            create = True
        data = update(data, pillar_data, create=create)
        return data

    @staticmethod
    def other_aliases(data, state_id, state_name, other_data=None):
        '''
        other_data can be provided in a loop in the state file like follows:

            $for name, values in pillar('users', {}).items():
                # self.update(values) will update ALL states with scope with
                # values and will return values wrapped in a DataWrapper with
                # allows dot notation access.  In order to access dictionary
                # directly within a DataWrapper, add ._data.  For example:
                # values._data.update(other)

                values = self.update(values)

        :param YSOrderedDict data: De-serialized script_data (nested)
        :param str state_id: State id key in `data[state_id]`
        :param str state_name: State name key in `data[state_id][state_name]`
        :param dict other_data: Provided from template via python call
        :return: other_data with modified __pillar_data__ if alias matched

        Once self.update(values) is called; we end up here, updating all the
        state objects in scope.

        If an alias exists, the aliased value will be returned to allow access
        to the other_data without having to use the state file (sls) structure,
        otherwise the a state structure will be implemented to retrieve the
        other_data from state_id.state.name keys

        This Allows shorter path names to values when looking up pillar values
        and also allow mixing of different state types within the same pillar_id.

        In the example below, user.user is aliased to null so when looking up
        values for user.user.uid we only need the structure to look like:

        users - state file:
        -------------------
        user:
          user:
          - __id__:         $'{0}_user'.format(user.user.name)
          - __alias__:      None
          - uid:            null
          - name:           null
          - gid:            null
          - gid_from_name:  False

        pillar file:
        ------------
        users:
          mel:
            uid: 400
            createhome: True

        instead of the default of:
        --------------------------
        users:
          mel:
            user.user:
              uid: 400
              createhome: True

        user.user.uid is the id.state.value in the state file.  they must be the
        same or aliased so values can be automatically found.

        NOTE:
        Any values in the pillar will then over ride any set in the
        state file.  Values can exist in the pillar that are not in the
        state file.  As shown in the above example, the pillar contains the
        createhome=True value, so even though it is not defined in the state
        file it will be applied in the final state since it's a valid
        value for the user creation state
        '''
        if not other_data:
            other_data = {}
        pillar_data = data.get('__pillar_data__', {})
        data['__pillar_data__'] = other_data

        pillars = yamlscript_utils.Schema.pillars()
        yamlscript_utils.set_alias(data, pillars, state_id, state_name)

        # Get generated data from alias, then reset to original state
        other_data = data['__pillar_data__']
        data['__pillar_data__'] = pillar_data
        return other_data


class Render(object):
    '''
    Contains all the methods and logic required to parse de-serialized
    yamlscript data and generate salt_data state objects.
    '''
    _stack_forloop = []
    _stack_if = []
    _locals = {}
    _globals = {}
    data = None
    index = {}

    # yamlscript private keys
    # private keys ae ones that should not get modified
    yamlscript_private_keys = [
        '__yamlscript__',
        '__fun__',
        '__argspec__',
        '__pillar__',
        '__alias__',
        '__pillar_data__',
    ]

    # yamlscript keys
    yamlscript_keys = [
        '__id__',
    ]
    yamlscript_keys.extend(yamlscript_private_keys)

    def __init__(self, script_data, sls_type, _globals):
        '''
        Renders the provided de-serialized yamlscript data recursively until
        all the required salt data states have been generated.

        Nothing is returned since the salt_data state objects reside in the
        `pyobjects Registry` which the salt renderer function will retreive
        and return to the salt renderer engine for processing.

        :param YSOrderedDict script_data: De-serialized script_data
        :param dict _globals: yamlscript and pyobjects globals used by this
        class as well as python execution and evaluation
        '''
        self.sls_type = sls_type

        # Pillars and templates store their data in salt_data
        self.salt_data = YSOrderedDict()

        # Set gloabl namespace so we have access to pyobjects state
        # function and convenience methods
        self._globals.update(_globals)
        globals().update(self._globals)

        # Data holds all the state contents and provides the ability to
        # merge, update and manipulate the script_data
        data = Data(copy.deepcopy(script_data))
        self.data = data

        # Set _locals vars that will be accessible to template
        self._locals = self.data._locals
        self._locals['data'] = self.data
        self._locals['self'] = self

        # Start parsing the script_data to generate salt_data state objects
        self.parse(self.data._script_data)

    def parse(self, data):
        '''
        Recursively parsed all the scipt_data that was de-serialized from the
        yamlscript template.

        There are 2 paths available top parse; either yaml or commands including
        python.  Command objects often have more command objects and yaml
        objects embeded in them and will recursively parse until all the
        salt state objects are created.

        Each command is seperately handled to carry out the desired statements.

        Nothing is returned from this method since all the created state objects
        are located in the `pyobjects Registry`.

        :param YSOrderedDict data: De-serialized script_data
        '''
        index_if = None
        for key_node, key_value in data.items():
            for name in key_value.keys():
                if hasattr(key_value, '__index__'):
                    self.index = key_value.__index__.get(name, {})
                else:
                    self.index = {}

                if '__yamlscript__' in key_value.keys():
                    command = key_value.pop('__yamlscript__')
                    self.index = command['index']

                    # Most commands except 'python' need index adjusted since we add an
                    # extra line of code within
                    self.index['key_start_line_offset'] = -1

                    # clear 'if' stack
                    if index_if is not None and command['type'] not in ['elif', 'else'] and self._stack_if:
                        index_if = None
                        self._stack_if.pop()
                    # for
                    if command['type'] == 'for':
                        # For loop will reset values to default at end of each loop
                        self._locals['__data__'] = key_value
                        self._stack_forloop.append(copy.deepcopy(key_value))
                        cmd = '{0}:\n    self.parse(__data__)\n    self._forloop_reset()\n'.format(command['statement'])
                        self.execute(cmd)
                        if self._stack_forloop:
                            self._stack_forloop.pop()
                    # if
                    elif command['type'] == 'if':
                        index_if = len(self._stack_if)
                        self._stack_if.append(False)
                        self._locals['__data__'] = key_value
                        cmd = '{0}:\n    self.parse(__data__)\n    self._stack_if[-1] = True\n'.format(
                            command['statement'])
                        self.execute(cmd)
                    # elif
                    elif command['type'] == 'elif':
                        if index_if is not None and not self._stack_if[index_if]:
                            self._locals['__data__'] = key_value
                            cmd = '{0}:\n    self.parse(__data__)\n    self._stack_if[-1] = True\n'.format(
                                command['statement'][2:])
                            self.execute(cmd)
                    # else
                    elif command['type'] == 'else':
                        if index_if is not None and not self._stack_if[index_if]:
                            self._locals['__data__'] = key_value
                            cmd = 'self.parse(__data__)\nself._stack_if[-1] = True\n'.format(command['statement'])
                            self.execute(cmd)
                    # with
                    elif command['type'] == 'with':
                        def exec_with(node, statement):
                            'Execute `with` statement'
                            self._locals['__data__'] = node
                            cmd = '{0}: self.parse(__data__)\n'.format(statement)
                            self.execute(cmd)
                        if command.get('content', None) is not None:
                            # `with` statement that includes yaml code
                            # Create the real final key_value for raw 'with' key_value
                            state_object = self.add(key_value, key_value.keys()[0],
                                                    key_value[key_value.keys()[0]].keys()[0])
                            # Now parse the included salt data using 'with' context of state_object
                            self._locals['state_object'] = state_object
                            exec_with(command['content'], 'with state_object')
                        else:
                            # `with` statement that includes a pyobjects state object
                            exec_with(key_value, command['statement'])
                    elif command['type'] == 'python':
                        self.index['key_start_line_offset'] = 0
                        self.execute(command['statement'])
                    else:
                        # command not implemented
                        pass
                    break
                else:
                    # Create the real final state
                    self.add(data, key_node, name)

    def process_sls_imports(self, code):
        '''
        Process our sls imports

        We allow pyobjects users to use a special form of the import statement
        so that they may bring in objects from other files. While we do this we
        disable the registry since all we're looking for here is python objects,
        not salt state data.
        '''
        client = salt.fileclient.get_file_client(__opts__)
        template = StringIO.StringIO(code)

        # Our import regexes
        FROM_RE = r'^\s*from\s+(salt:\/\/.*)\s+import (.*)$'
        IMPORT_RE = r'^\s*import\s+(salt:\/\/.*)$'

        template_data = []
        Registry.enabled = False
        for line in template.readlines():
            line = line.rstrip('\r\n')
            matched = False
            for RE in (IMPORT_RE, FROM_RE):
                matches = re.match(RE, line)
                if not matches:
                    continue

                import_file = matches.group(1).strip()
                try:
                    imports = matches.group(2).split(',')
                except IndexError:
                    # if we don't have a third group in the matches object it means
                    # that we're importing everything
                    imports = None

                state_file = client.cache_file(import_file, self._globals['saltenv'])
                if not state_file:
                    raise ImportError("Could not find the file {0!r}".format(import_file))

                with open(state_file) as f:
                    state_contents = f.read()

                state_locals = {}
                if sys.version_info[0] > 2:
                    # in py3+ exec is a function
                    exec(state_contents, self._globals, state_locals)
                else:
                    # prior to that it is a statement
                    exec state_contents in self._globals, state_locals

                if imports is None:
                    imports = state_locals.keys()

                for name in imports:
                    name = name.strip()
                    if name not in state_locals:
                        raise ImportError("{0!r} was not found in {1!r}".format(
                            name,
                            import_file
                        ))
                    self._globals[name] = state_locals[name]

                matched = True
                break

            if not matched:
                template_data.append(line)

        final_template = "\n".join(template_data)

        # re-enable the registry
        Registry.enabled = True

        return final_template

    def execute(self, code):
        '''
        Executes python code within yamlscript template using locals that
        contain all the default state objects that can be read or modified
        as well as access to most python and salt modules.

        :param str code: Python string to execute
        :raises RenderError: if something fails a special mode of the error
        renderer will mark the actual line of code that has an error within the
        template code
        '''
        # Process any sls imports first
        code = self.process_sls_imports(code)

        try:
            if sys.version_info[0] > 2:
                # in py3+ exec is a function
                exec (code, self._globals, self._locals)  # pylint: disable=W0122
            else:
                # prior to that it is a statement
                exec code in self._globals, self._locals  # pylint: disable=W0122
        except RenderError:
            raise
        except Exception as error:
            raise RenderError(error, index=self.index, mode='exec')

    def evaluate(self, code):
        '''
        Used to evaluate scaller values to try to match script tokens
        to variables stored within self._locals

        :param str code: A scalar text value to be evaluated
        :return: Either the original values or the a matched a value in _locals
        :rtype: str
        '''
        return eval(code, self._globals, self._locals)

    def evaluate_state_items(self, state):
        '''
        Looks for scalar values that begin with '$' and attempts to evaluate
        the value again the local stack.

        If a value begins with '$$', it has been escaped and therefore will
        be skipped

        :param dict state: The state scalar values of a state
        :return: the evaluated values including and nested lists or dictionaries
        :rtype: YSOrderedDict
        '''

        def replace(value):
            '''
            Recursively find values to replace that may be hiding in lists
            or nested dictionaries.

            Any string that are found are evaluated against values set in
            template and are replaced with actual value

            :param value: Scalar value
            :return: the evaluated value including and nested lists or dictionaries
            :rtype: YSOrderedDict
            '''
            try:
                # pylint: disable=W0631

                # Normally you escape a wanted dollar sign $ with $$, but
                # sometimes a string starts with two $$, so we need to
                # esacpe a double $$ with \
                if isinstance(value, str) and value.startswith('\$$'):
                    # Leave as is if its a pillar; cause state will strip it
                    if self.sls_type == 'pillar':
                        new_value = value
                    else:
                        new_value = value = value[1:]  # strip \
                elif isinstance(value, str) and value.startswith('$$'):
                    # Leave as is if its a pillar; cause state will strip it
                    if self.sls_type == 'pillar':
                        new_value = value
                    else:
                        new_value = value = value[1:]  # strip $
                elif isinstance(value, str) and value.startswith('$'):
                    value = value[1:]
                    new_value = self.evaluate(value)
                elif isinstance(value, list):
                    new_value = []
                    for list_value in value:
                        new_value.append(replace(list_value))
                elif isinstance(value, dict):
                    new_value = {}
                    for key, item_value in value.items():
                        new_value[key] = replace(item_value)
                else:
                    new_value = value

                if value != new_value:
                    return replace(new_value)
                else:
                    return new_value

            except (NameError, TypeError, SyntaxError, AttributeError):
                pass

        if isinstance(state, dict):
            for key, value in state.items():
                if key in self.yamlscript_private_keys:
                    state[key] = value
                else:
                    new_value = replace(value)
                    state[key] = new_value
        else:
            state = replace(state)

        return state

    def _forloop_reset(self):
        '''
        Resets forloop scope to a fresh state for next iteration; called
        automatically by forloop when its completes each loop cycle

        self.data.update() is called which will reset all states in scope
        to default values so they are ready to use again on the next loop
        cycle.
        '''
        data = copy.deepcopy(self._stack_forloop[-1:][0])
        data = self.data.update(data)
        self._locals['__data__'] = data

    def update(self, other_data):
        '''
        Update ALL states with scope with values provided and will return the
        values wrapped in a DataWrapper which will allows dot notation
        access to the values.

        The attribute `_data`` is reserved and stores the underlying dictionary.
        This is also how to directly access the underlying dictionary in order
        to use functions provided by the dictionary like update or pop.  For
        example:

        .. code-block:: python

            values._data.update(other)
            values._data.pop(key)

        :param dict other_data: Provided from template via python call
        :return: A DataWrapper (other_data)
        :rtype: DataWrapper
        '''
        self.data.update(self._locals['__data__'], other_data)
        return DataWrapper(other_data)

    def add(self, data, state_id, state_name):
        '''
        Prepares data then calls `add_smart_state`.  The data scalars and any
        nested values are first evaluated against self._locals where variables
        set within the template are replaced with the actual values.  If the
        __id__ changes from a replacement, the new __id__ will be used to
        create the final state object.

        :param dict data: Data `dict` or `DataWrapper` containing raw state structure
        :param str state_id: State id key in `data[state_id]`
        :param str state_name: State name key in `data[state_id][state_name]`
        :return: The final salt_data object
        :rtype: salt.utils.pyobjects.State
        '''
        # Keep the original state intact in case it needs to be re-used
        scalar = copy.deepcopy(data[state_id][state_name])

        # Lets see if any values need to be eval'd
        try:
            scalar = self.evaluate_state_items(scalar)

            # Only states can change their id
            if self.sls_type == 'state':
                state_id = scalar.get('__id__', state_id)

            data.setdefault(state_id, {}).setdefault(state_name, {})
            data[state_id][state_name] = scalar
            self.data.add(data, state_id, state_name)

            # State handling
            if self.sls_type == 'state':
                # Create the real final salt_data state
                state_object = self.add_smart_state(data, state_id, state_name)
                return state_object

            # Pillar handling
            # TODO: Combine with template
            # XXX: - Really should not be writing directly to __pillar__.  Its being written
            #        to so evaluate function can pick up on any changes.
            #      - Could make a deep copy of original to use
            elif self.sls_type == 'pillar':
                # We can overwite state_id everytime since
                # self.data._states[state_id] will always have the most upto
                # date values
                self._globals['__pillar__'][state_id] = self.data._states[state_id].get('pillar', {})
                self.salt_data[state_id] = self.data._states[state_id].get('pillar', {})

            # Template handling
            elif self.sls_type == 'template':
                self.salt_data[state_id] = self.data._states[state_id].get('template', {})

        except KeyError as error:
            # Most likely a state was removed with inline python
            msg = 'Can not access state values [{0}][{1}]: KeyError: {2}'.format(state_id, state_name, str(error))
            raise RenderError(msg, index=self.index)

    def add_smart_state(self, data, state_id, state_name):
        '''
        Adds and returns a new state using values from `data` dictionary.

        :param dict data: Data `dict` or `DataWrapper` containing raw state structure
        :param str state_id: State id key in `data[state_id]`
        :param str state_name: State name key in `data[state_id][state_name]`
        :return: The final salt_data object
        :rtype: salt.utils.pyobjects.State
        '''
        # Confirm we have correct data set
        data = find_state(data, state_id, state_name)
        if isinstance(data, DataWrapper):
            data = data._data

        try:
            defaults = data[state_id][state_name]
        except KeyError as error:
            msg = 'Can not access state values [{0}][{1}]: KeyError: {2}'.format(state_id, state_name, str(error))
            raise RenderError(msg, index=self.index)

        if '__fun__' not in defaults.keys():
            msg = 'Can not determine function for [{0}][{1}]'.format(state_id, state_name)
            raise RenderError(msg, index=self.index)

        state_function = get_state_function(state_name, defaults['__fun__'])

        # Remove name(s) if they are None
        if defaults.get('name', None) is None:
            defaults.pop('name', None)
        if defaults.get('names', None) is None:
            defaults.pop('names', None)

        # Can't have a None value for require
        if 'require' in defaults.keys() and defaults['require'] is None:
            defaults['require'] = []

        for k in self.yamlscript_keys:
            defaults.pop(k, None)

        # Create final state
        return state_function(state_id, **defaults)


def render(template, saltenv='base', sls='', **kwargs):
    '''
    Creates an OrderedDict representing id's with states and values from a
    #!yamlscript state (sls) template.

    Yamlscript is a mix of python and yaml using yamls structured human readable
    format.
    '''
    # Keep track of stack during include statements
    yamlscript_utils.Cache(__context__)
    yamlscript_utils.Cache.set(sls, sls)

    # Set some global builtins in yamlscript_utils
    def getvar(var):
        return kwargs.get(var, globals().get(var, {}))

    salt = getvar('__salt__')
    states = getvar('__states__')
    pillar = getvar('__pillar__')
    grains = getvar('__grains__')
    opts = getvar('__opts__')

    yamlscript_utils.__opts__ = opts
    yamlscript_utils.__states__ = states
    yamlscript_utils.__pillar__ = pillar

    # Detect if we are running a template, pillar or state
    if 'sls_type' not in kwargs.keys():
        if states:
            kwargs['sls_type'] = 'state'
        else:
            kwargs['sls_type'] = 'pillar'

    # Convert yaml to ordered dictionary
    deserialize = yamlscript_utils.Deserialize(
        template,
        saltenv=saltenv,
        sls=sls,
        **kwargs
    )
    script_data = deserialize.generate(
        deserialize.state_file_content,
        yamlscript_utils.YSOrderedDict()
    )
    yamlscript_utils.Cache.set(sls, deserialize)

    # Set _globals; used for evaluation of code
    if kwargs['sls_type'] == 'state':
        # Call pyobjects to build globals and provide functions to create states
        pyobjects = kwargs['renderers']['pyobjects']
        _globals = pyobjects(template, saltenv, sls, salt_data=False, **kwargs)
    else:
        # add some convenience methods to the global scope as well as the "dunder"
        # format of all of the salt objects
        try:
            _globals = {
                # the "dunder" formats are still available for direct use
                '__salt__': salt,
                '__pillar__': pillar,
                '__grains__': grains,

                'pillar': pillar.get,
            }
            if salt:
                # salt, pillar & grains all provide shortcuts or object interfaces
                _globals['grains'] = salt['grains.get']
                _globals['mine'] = salt['mine.get']
                _globals['config'] = salt['config.get']
        except NameError:
            raise

    # Use copy of __pillar__ and __grains__ dictionaries
    salt_vars = ['__pillar__', '__grains__']
    for var in salt_vars:
        _globals[var] = copy.deepcopy(_globals[var])

    # Additional globals
    _globals['__context__'] = dict(state_list=deserialize.state_list)
    _globals['saltenv'] = saltenv

    # Can't use pyobject global 'salt' since we need to import salt classes
    _globals.pop('salt', None)

    # Render the script data that was de-serialized into salt_data
    rendered = Render(script_data, kwargs['sls_type'], _globals=_globals)

    # If its a pillar or template, return it now
    if kwargs['sls_type'] in ['pillar', 'template']:
        return rendered.salt_data

    salt_data = Registry.salt_data()

    # Run tests if state file provided a test file location.  Tests will
    # compare the salt_data to an expected result retreived from test file
    if len(yamlscript_utils.Cache.all()) == 1:
        if deserialize.test_data:
            yamlscript_utils.test(salt_data, deserialize.test_data, sls=sls)
        # Clean up cache
        yamlscript_utils.Cache.pop(sls)

    return salt_data

#def render(template, saltenv='base', sls='', **kwargs):
def render_yamlscript_tmpl(tmplstr, context, tmplpath=None):
    '''
    Parses a yaml formatted template and replaces values with pillar data or
    user provided script data, using any defaults within.

    Yamlscript is a mix of python and yaml using yamls structured human readable
    format.
    '''
    kwargs = {}
    sls_type = 'template'
    kwargs['sls_type'] = sls_type
    kwargs['__opts__'] = context['opts']
    kwargs['__pillar__'] = context['pillar']

    # Render the templae
    salt_data = render(StringIO.StringIO(tmplstr),
                       saltenv=context['saltenv'],
                       sls=context['source'],
                       **kwargs
                       )

    outputters = salt.loader.outputters(context['opts'])
    out = outputters['yaml']

    # Convert from YSOrderedDict to a salt OrderDict
    # Then format as YAML
    salt_data = out(convert(salt_data))

    # Indent by 2 spaces
    salt_data = salt_data.replace('- ', '  - ')

    return salt_data

'''
TESTS:
======
states:
--local --out=yaml state.show_sls tests_yamlscript test

pillars:
Same as above; but add #!yamscript shebang to user.sls pillar file

tempaltes:
--local state.highstate -l debug

TODO:
=====

- Ability to set pillar base.  Not sure how we doing it now for users, but I think
  the proper term would be pillar_base not alias or such

FOR TEMPLATES
-------------
- Re-work aliases.  Implement base as well?
  - Should we get rid of automatic detection?  Like pass what we want, and allow it to be over written
    - set_alias(state_id, state_name, alias)
      - where alias is:
        - string to locate it keynode=user alias=user_names, or user_name:machine1
        - False -- disabled
        - None -- base; so pillar would be user
      - then, set_alias function will see if a rule already exists, and use it if it does, so
        if auto was set to False or its listed in disabled, it will be disabled
      - same for enabled, it will be enabled even if we say False
    - get_pillar_data(state_id)
      - now an alias has been set it, pillar data will attempt to be located and returned
    - so, thats basicly how it already works, but there is not way to set easy while taking into
      consideration rules set by user
  - If aliases are written in self.pillars, we can use that instead of writing to __pillar_data__??
    - Considerations would be duplicate keys?  Should not happen though
  - Can we get rid of update and merge then?  Or greatly simplify them.  piller.get will return
    default values if pillar does not exist

- Add salt logging as well as comments in state output that pillar was automatically used, or denied
  by rule, etc

- Test various types of pillar replacements (dict, list, nested dict).  Maybe just set up
  an alias in advance

- Pre-parse and convert # comments into $comment blocks blank lines into $blank ans spaces into $space

- Post parse to convert back to be able to retain comments, etc in yaml scripts
  - Don't support inline comments since it could break flow?

- Create a YSOrderedDict dumper so I don't need to convert to OrderedDict

FOR PILLARS
-----------
- Seems like yamlscript in pillars work, but then salt can not find the SLS state files, so it exits;
  something about statefile can't be found

- Combine template and pillar code where possible

- Consider not writing to __pillar__ directly!  What happens if it fails, then partial pillar in memory.

GENERAL
-------
- Try to seperate out core so it can be used for other projects.  Use an adapter for pillar or similar
  types of machinery

- modules, outputters, utils, renderers  -- separate into those sections

VALIDATION
----------
- Plug in voluptuous as an adapter to be able to validate
  - right now state validation happens at the end; make that a plugin so other things can be
    validated, so in other word we would not have to 'contine' pillars and templates, let it
    go to see if there is an adapter, and if not continue!
    - that would allow templates to be futher parsed which would allow loops, etc?

'''

# XXX: Template
import collections
import salt.utils.odict
def convert(dict_):
    'converts any dictionary and nested dictionaries to a dict'
    for key, value in dict_.iteritems():
        if isinstance(value, collections.Mapping):
            dict_[key] = convert(dict_[key])
        elif isinstance(value, list):
            for element in value:
                if isinstance(element, collections.Mapping):
                    value[value.index(element)] = convert(element)
    return salt.utils.odict.OrderedDict(dict_)

from salt.utils.templates import TEMPLATE_REGISTRY, wrap_tmpl_func
YAMLSCRIPT = wrap_tmpl_func(render_yamlscript_tmpl)
TEMPLATE_REGISTRY['yamlscript'] = YAMLSCRIPT
