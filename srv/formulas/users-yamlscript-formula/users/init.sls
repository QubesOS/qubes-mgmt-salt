#!yamlscript
#

$comment: |

    ============================================================================
    Overview of Features:
    ============================================================================
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

    - requisites are automatically calculated just by using 'with' statement
      and nesting (indenting) underneath

    - test mode available to test state files against a test file before deployment

    - support for pyobjects maps; yaml format available for creating them

    - tracking of error positions in python snippets that will display real line number
      error is one in state file compare to a generic stack trace related to
      yamlscript source files

    Cavaets:
    - You must escape any scalar value that begins with a '$' with another
      '$' so to produce '$4.19', escape like this: '$$4.19'


    ============================================================================
    Pillars:
    ============================================================================
    - Auto pillar mode is disabled by default.  The yamlscript renderer will
      attempt to locate pillar data automatically based on the 'id' of the state
      file when auto mode is enabled or individual state id is listed in the
      $pillars.enabled list.

    - The pillar structure must match state structure unless a state-side pillar
      map is set.

    - Place __pillar__ within an individual state to override any defaults.

    - A pillar alias may be used to shorten paths in pillar data, or
      when combining multiple types of state data within the same pillar data.

    Important NOTE:

      Note that any values set in pillar WILL override any defaults set withing
      the state file with the exception of values set by python code.

      Process:
        state defaults  <-- sls defaults  <-- pillar data  <-- generated code

    The following is an example of shortening the pillar path:

      --------------------------------------------------------------------------
      pillar data (/srv/pillar/users/init.sls)
      --------------------------------------------------------------------------
      users:
        mel:
          user:
            user:
              gid: 400
              createhome: True

      - OR... shorten the pillar path and use an alias of 'user.user'

      users:
        mel:
          user.user:
            gid: 400
            createhome: True

      - OR... shorten the pillar path even more with an alias of 'None'

      users:
        mel:
          gid: 400
          createhome: True


    ============================================================================
    Pillars state file declaration:
    ============================================================================
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

      --------------------------------------------------------------------------
      Yamlscript state file (/srv/salt/users/init.sls):
      --------------------------------------------------------------------------
      #!yamlscript
      $pillars:
          auto: True
          aliases:
            - user.user: None
            - ssh.directory: ssh

      --------------------------------------------------------------------------
      Pillar data (/srv/pillar/users/init.sls):
      --------------------------------------------------------------------------
      users:
        mel:
          gid: 400
          createhome: True
          ssh:
            save_keys: False


    ============================================================================
    States:
    ============================================================================
    - Every state can contain additional keys / value pairs to provide hints
      to the yamlscript renderer parser

    __id__:
        Override the supplied state id with scalar value.  This is useful
        to prevent duplicate state id's when creating states dynamicly:

            $'{0}_group'.format(group.group.name)

    __pillar__:
        Override `auto`, `disabled` and `enabled` declarations.

        state_id:
          state_name:
            __pillar__: True|False|<string>

        True:   Will attempt to merge pillar data
        False:  Will not attempt to merge pillar data
        string: string value of the pillar_id to use (map)

    __alias__ declaration:
        An `__alias__` declaration can be set to change the path to
        pillar_data.  Only the path needs to be set since state_id and
        state_path can be obtained.

        state_id:
          state_name:
            __alias__: null
            __alias__: user.user


    ============================================================================
    Yamlscript Commands:
    ============================================================================
    $python: |
        Embed python script into yaml. Indent 4 spaces. Python can be embeded
        in multiple locations without fear of using a duplicate key.

        All variables and functions created within the embeded python script is
        available to all states that follow the code which can be referenced
        from the state from within the scalar by starting the scalar with a
        dollar '$' sign.

        Likewise, the python script can directly set values to individual
        states by accessing them via dot notation via
        <state_id>.<state_name>.<key>.

        Pillar data can be manually loaded and accessed by dot-notation so long
        as the pillar data is dictionary formed as well by updating the
        yamlscript renderer:

        Individual states can also access other state values in the same manner.

          $python |
              # Update the yamlscript renderer with manually obtained pillar
              # data.  The update command will return a dot.notation accessable
              # dictionary to allow convient access as well as merge any pillar
              # data with the states within the sls file based on pillar and
              # alias rules.
              pillar_data = pillar('custom_pillar, {})
              self.update(pillar_data)

              # Directly set the name of the group
              group.group.name = 'apache'

              # Set gid so state can reference and use it
              gid = 3000

          group:
            group.present:
            - __id__: group_apache
            - name:   null
            # Use the value defined in python script for gid
            - gid:    $gid

          state_id:
            state_name.function:
              # Use the group name as Directly set in python as this state id
              - __id__: $'{0}_group'.format(group.group.name)

    $for:
        Iterate over some object. States may be included within the loop by
        indenting them

        # Loop through all groups provided in pillar and create dynamic states
        # to create them
        $for name in pillar('absent_groups', []):
          absent_groups:
            group.absent:
              - __id__: $'{0}_absent_group'.format(name)
              - name:   $name

    $with:
        Allows any state indented below to become an automatic requisites which
        automatically sets the indented state to require the state

    $if:
    $elif:
    $else:
        Conditionals will only include indented state if condtions are met

        $if user.user.createhome and user.user.home is not None:
          file.directory:
          - __id__:           $'{0}_user'.format(user.user.name)
          - name:             $user.user.home

    $include: XXX: Provide more detailed explaination
        Includes another state file and is not parsed by yamlscript directly

    $extend: XXX: Provide more detailed explaination
        Extend an existing state file.  Yamlscript does not parse the file.

    $import: XXX: Provide more detailed explaination
        Includes another state file and is parsed by yamlscript directly.  All
        states imported are directly able to be referenced

    $pillars:
        Explained above

    $test_file:
        A test file can contain expected final highstate results that can be
        used to test and verify state files.  See sample test files inculded
        with the yamlscript formula for better understanding of usage.

    $defaults:
        defaults can be set as True or False. If True, all state fields are
        prepopulated with the states default variables and values which may be
        useful when using aliased (short) pillar names to prevent additional
        pillar data from being merged.

    $comment:
        Just allows a nicely formatted YAML comment block.  Future versions
        of yamlscript will convert regular style comments starting with the
        pound/number sign '#' to $comment when loading the yaml and then
        convert back when dumping to allow regular comments persist.

        Normally comments are lost since they are not parsed and this would not
        be desired in some use cases.

# Will set all the default values from salt; allows short pillar descriptions
$defaults : True

# Defualt user group to use if you don't add them in pillar
$python: default_users_group = 'users'

$include: users.sudo

# See notes above
$pillars:
  auto: False
  disabled: []
  enabled:
    - /etc/sudoers.d
    - sudoer_file

# Main group add loop
$for name, values in pillar('groups', {}).items():
  $python: |
      if values is None:
          values = {}
      values.update(name=name)
      values = self.update(values)
      group.group.name = name

  group:
    group.present:
    - __id__:           $'{0}_group'.format(group.group.name)
    - __alias__:        null
    - name:             null
    - gid:              null

# Absent groups
$for name in pillar('absent_groups', []):
  absent_groups:
    group.absent:
    - __id__:           $'{0}_absent_group'.format(name)
    - name:             $name

# Absent users
$for name in pillar('absent_users', []):
  absent_users:
    user.absent:
    - __id__:           $'{0}_absent_user'.format(name)
    - name:             $name

# Main user add loop
$for name, values in pillar('users', {}).items():
  $python: |
      if values is None:
          values = {}
      values.update(name=name)

      # self.update(values) will update ALL states with scope with values
      # and will return values wrapped in a ContentWrapper with allows dot
      # notation access.  In order to access dictionary directly within
      # a ContentWrapper, add ._data.  For example:
      values = self.update(values)
      user.user.name = name

      # Set home directory location now
      if user.user.createhome and user.user.home is None:
          user.user.home = '/home/{0}'.format(user.user.name)

      # TODO:  just set user.user.group.name in yaml;
      #          - test with null value and default_users_group
      #
      # If `default_users_group` is `None` and `user.group.name` is `None`
      # (no primary group was set in pillar), one will be created based on the
      # user name
      if default_users_group is None:
        pass # Create one based on something

      # Set gid... considerations:
      #   gid_from_name: False
      #   primary_group: {name: None, gid: None}
      #   gid: None
      if user.user.gid_from_name and user.user.uid is not None:
          user.user.gid = user.user.uid
      elif user.group.gid is not None:
          user.user.gid = user.group.gid
      elif user.user.gid is None:
          user.user.gid_from_name = True

      if user.group.name is None and user.user.gid_from_name:
          user.group.name = '{0}'.format(user.user.name)

      # User primary group name
      if user.group.name is not None:
          user.user.groups.append(user.group.name)

      #if sudo.user and sudo.groups:
      #    for g in sudo.groups:
      #        if g not in user.user.groups:
      #            user.user.groups.append(g)

  user:
    group.present:
    - __id__:           $'{0}_user'.format(user.user.name)
    - name:             $default_users_group
    - gid:              null
    user.present:
    - __id__:           $'{0}_user'.format(user.user.name)
    - __alias__:        null
    - name:             null  # Not changable
    - uid:              null
    - gid:              null
    - gid_from_name:    False
    - groups:           []
    - optional_groups:  []
    - remove_groups:    True
    - home:             null
    - createhome:       True
    - password:         null
    - enforce_password: True
    - shell:            null
    - unique:           True
    - system:           False
    - fullname:         null
    - roomnumber:       null
    - workphone:        null
    - homephone:        null
    - date:             null
    - mindays:          null
    - maxdays:          null
    - inactdays:        null
    - warndays:         null
    - expire:           null

    $if user.user.createhome and user.user.home is not None:
      file.directory:
      - __id__:           $'{0}_user'.format(user.user.name)
      - name:             $user.user.home
      - user:             $user.user.name
      - group:            $user.group.name
      - makedirs:         True
      - mode:             770

  $for g in user.user.groups:
    $if g != user.group.name:
      user_groups:
        group.present:
        - __id__:           $'{0}_{1}_group'.format(user.user.name, g)
        - name:             $g

  $if user.user.createhome and user.user.home and values.ssh.save_keys:
    $with File('{0}_user'.format(user.user.name), 'require'):
      $with ssh_directory:
        file:
        - __id__:           $'{0}/.ssh'.format(user.user.home)
        - __alias__:        ssh
        - user:             $user.user.name
        - group:            $user.group.name
        - makedirs:         true
        - mode:             700
        - directory

        ssh_private_key:
          file:
          - __id__:           $'{0}/.ssh/id_{1}'.format(user.user.home, values.ssh.key_type)
          - name:             $'{0}/.ssh/id_{1}'.format(user.user.home, values.ssh.key_type)
          - user:             $user.user.name
          - group:            $user.group.name
          - contents_pillar:  $'users:{0}:ssh:keys:private'.format(user.user.name)
          - makedirs:         true
          - mode:             600
          - managed

        ssh_public_key:
          file:
          - __id__:           $'{0}/.ssh/id_{1}.pub'.format(user.user.home, values.ssh.key_type)
          - user:             $user.user.name
          - group:            $user.group.name
          - contents_pillar:  $'users:{0}:ssh:keys:public'.format(user.user.name)
          - makedirs:         true
          - mode:             644
          - managed

        $if auth_present.ssh_auth.name or auth_present.ssh_auth.names:
          auth_present:
            ssh_auth.present:
              - __id__:         $'{0}_user_auth_present'.format(user.user.name)
              - user:           $user.user.name

        $if auth_absent.ssh_auth.name or auth_absent.ssh_auth.names:
          auth_absent:
            ssh_auth:
              - __id__:         $'{0}_user_auth_absent'.format(user.user.name)
              - user:           $user.user.name
              - absent

