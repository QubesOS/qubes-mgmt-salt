# -*- coding: utf-8 -*-
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

{%- from "qubes/vmtype.jinja" import vmtype %}

salt:
  clean_config_d_dir: False
  install_packages: True
  
  {% if grains['os']|lower == 'fedora' %}
  repotype: fedora
  {% endif %}

  # ────────────────────────────────────────────────────────────────────────────
  # reactor
  # ────────────────────────────────────────────────────────────────────────────
  reactor:
    - 'minion_start':
      - /srv/reactor/sync_all.sls
      - /srv/reactor/import_keys.sls

  minion:
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                                CUSTOM
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ──────────────────────────────────────────────────────────────────────────
    # Root formula directories
    # Default: /srv/formulas
    # ──────────────────────────────────────────────────────────────────────────
    formula_dirs:
      - /srv/formulas
      - /srv/user_formulas

    # ──────────────────────────────────────────────────────────────────────────
    # Topd configuration path locations
    # ──────────────────────────────────────────────────────────────────────────
    topd_dir_name: _topd
    topd_base_pillar: /srv/pillar
    topd_base_state: /srv/salt

    # ──────────────────────────────────────────────────────────────────────────
    # Node groups allow for logical groupings of minion nodes. A group consists
    # of a group name and a compound target.
    # nodegroups:
    #   group1: 'L@foo.domain.com,bar.domain.com,baz.domain.com and bl*.domain.com'
    #   group2: 'G@os:Debian and foo.domain.com'
    # ──────────────────────────────────────────────────────────────────────────
    nodegroups:
      dom0: 'G@virtual:Qubes'
      vm: 'P@virtual_subtype:Xen\sPV\sDomU'

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                         FILE DIRECTORY SETTINGS 
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # The Salt Minion can redirect all file server operations to a local
    # directory, this allows for the same state tree that is on the master to be
    # used if copied completely onto the minion. This is a literal copy of the
    # settings on the master but used to reference a local directory on the
    # minion.
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ──────────────────────────────────────────────────────────────────────────
    # Set the file client. The client defaults to looking on the master server
    # for files, but can be directed to look at the local file directory setting
    # defined below by setting it to local.
    # ──────────────────────────────────────────────────────────────────────────
    file_client: local
    
    # ──────────────────────────────────────────────────────────────────────────
    # The file directory works on environments passed to the minion, each
    # environment can have multiple root directories, the subdirectories in the
    # multiple file roots cannot match, otherwise the downloaded files will not
    # be able to be reliably ensured. A base environment is required to house
    #  the top file.
    # ──────────────────────────────────────────────────────────────────────────
    file_roots:
      base:
        - /srv/salt
      user:
        - /srv/user_salt
    
    # ──────────────────────────────────────────────────────────────────────────
    # By default, the Salt fileserver recurses fully into all defined
    # environments to attempt to find files. To limit this behavior so that the
    # fileserver only traverses directories with SLS files and special Salt
    # directories like _modules, enable the option below. This might be useful
    # for installations where a file root has a very large number of files and
    # performance is negatively impacted. Default is False.
    # ──────────────────────────────────────────────────────────────────────────
    fileserver_limit_traversal: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # The hash_type is the hash to use when discovering the hash of a file in
    # the local fileserver. The default is md5, but sha1, sha224, sha256, sha384
    # and sha512 are also supported.
    #
    # Warning: Prior to changing this value, the minion should be stopped and
    # all Salt caches should be cleared.
    # ──────────────────────────────────────────────────────────────────────────
    hash_type: md5
    
    # ──────────────────────────────────────────────────────────────────────────
    # The Salt pillar is searched for locally if file_client is set to local. If
    # this is the case, and pillar data is defined, then the pillar_roots need
    #  to also be configured on the minion:
    # ──────────────────────────────────────────────────────────────────────────
    pillar_roots:
      user:
        - /srv/user_pillar
      base:
        - /srv/pillar
        - /srv/pillar/base
      all:
        - /srv/pillar/all
      vm:
        - /srv/pillar/vm
      dom0:
        - /srv/pillar/test
      test:
        - /srv/pillar/test

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                         GIT FILESYSTEM SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ──────────────────────────────────────────────────────────────────────────
    # XXX: Missing from salt-formula
    # ──────────────────────────────────────────────────────────────────────────
    #fileserver_backend:
    #  - roots
    #  - git

    # ──────────────────────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────────────────────
    {% if vmtype == 'vm' %}
    gitfs_provider: dulwich
    
    # gitfs_remotes: []
    {% endif %}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                           LOGGING SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ──────────────────────────────────────────────────────────────────────────
    # The location of the minion log file.
    #
    # The minion log can be sent to a regular file, local path name, or network
    # location. Remote logging works best when configured to use rsyslogd(8).
    #
    # The URI format is:
    #   <file|udp|tcp>://<host|socketpath>:<port-if-required>/<log-facility>
    #
    # Examples:
    #   log_file: /var/log/salt/minion
    #   log_file: file:///dev/log
    #   log_file: udp://loghost:10514
    # ──────────────────────────────────────────────────────────────────────────
    # Double quote log stings to prevent parser errors
    log_file: /var/log/salt/minion
    key_logfile: /var/log/salt/key

    # ──────────────────────────────────────────────────────────────────────────
    # The level of messages to send to the console.
    # One of 'garbage', 'trace', 'debug', info', 'warning', 'error', 'critical'.
    # Default: 'warning'
    # ──────────────────────────────────────────────────────────────────────────
    log_level: warning
    
    # ──────────────────────────────────────────────────────────────────────────
    # The level of messages to send to the log file.
    # One of 'garbage', 'trace', 'debug', info', 'warning', 'error', 'critical'.
    # If using 'log_granular_levels' this must be set to the highest desired
    # level.
    # Default: 'warning'
    # ──────────────────────────────────────────────────────────────────────────
    log_level_logfile: warning
    
    # ──────────────────────────────────────────────────────────────────────────
    # The date and time format used in log messages. Allowed date/time formating
    # can be seen here: http://docs.python.org/library/time.html#time.strftime
    # ──────────────────────────────────────────────────────────────────────────
    log_datefmt: '"%H:%M:%S"'
    log_datefmt_logfile: '"%Y-%m-%d %H:%M:%S"'
    
    # ──────────────────────────────────────────────────────────────────────────
    # The format of the console logging messages.
    #
    # Allowed formatting options can be seen at:
    #   http://docs.python.org/library/logging.html#logrecord-attributes
    # ──────────────────────────────────────────────────────────────────────────
    log_fmt_console: '"[%(levelname)-8s] %(message)s"'
    log_fmt_logfile: '"%(asctime)s,%(msecs)03.0f [%(name)-17s][%(levelname)-8s] %(message)s"'
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                         MINION MODULE MANAGEMENT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ──────────────────────────────────────────────────────────────────────────
    # Disable specific modules. This allows the admin to limit the level of
    # access the master has to the minion.
    # ──────────────────────────────────────────────────────────────────────────
    {% if vmtype == 'dom0' %}
    disable_modules:
      - git
    {% endif %}
    #disable_returners: []

    # ──────────────────────────────────────────────────────────────────────────
    # Modules can be loaded from arbitrary paths. This enables the easy
    # deployment of third party modules. Modules for returners and minions can
    # be loaded.
    # Specify a list of extra directories to search for minion modules and
    # returners. These paths must be fully qualified!
    # ──────────────────────────────────────────────────────────────────────────
    #module_dirs: []
    #returner_dirs: []
    #states_dirs: []
    #render_dirs: []
    #utils_dirs: []
    
    # ──────────────────────────────────────────────────────────────────────────
    # A module provider can be statically overwritten or extended for the minion
    # via the providers option, in this case the default module will be
    # overwritten by the specified module. In this example the pkg module will
    # be provided by the yumpkg5 module instead of the system default.
    # ──────────────────────────────────────────────────────────────────────────
    #providers:
    #  pkg: qubes-dom0-pkg`
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                            SECURITY SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ──────────────────────────────────────────────────────────────────────────
    # Enable "open mode", this mode still maintains encryption, but turns off
    # authentication, this is only intended for highly secure environments or
    # for # the situation where your keys end up in a bad state. If you run in
    # open mode you do so at your own risk!
    # ──────────────────────────────────────────────────────────────────────────
    open_mode: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # Enable permissive access to the salt keys.  This allows you to run the
    # master or minion as root, but have a non-root group be given access to
    # your pki_dir.  To make the access explicit, root must belong to the group
    # you've given access to. This is potentially quite insecure.
    # ──────────────────────────────────────────────────────────────────────────
    permissive_pki_access: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # The state_verbose and state_output settings can be used to change the way
    # state system data is printed to the display. By default all data is
    # printed.
    # The state_verbose setting can be set to True or False, when set to False
    # all data that has a result of True and no changes will be suppressed.
    # ──────────────────────────────────────────────────────────────────────────
    state_verbose: True
    
    # ──────────────────────────────────────────────────────────────────────────
    # The state_output setting changes if the output is the full multi line
    # output for each changed state if set to 'full', but if set to 'terse'
    # the output will be shortened to a single line.
    # ──────────────────────────────────────────────────────────────────────────
    state_output: highstate
    
    # ──────────────────────────────────────────────────────────────────────────
    # The state_output_diff setting changes whether or not the output from
    # successful states is returned. Useful when even the terse output of these
    # states is cluttering the logs. Set it to True to ignore them.
    # ──────────────────────────────────────────────────────────────────────────
    state_output_diff: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # Fingerprint of the master public key to double verify the master is valid,
    # the master fingerprint can be found by running "salt-key -F master" on the
    # salt master.
    # ──────────────────────────────────────────────────────────────────────────
    #master_finger: ''
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                        STATE MANAGEMENT SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ──────────────────────────────────────────────────────────────────────────
    # The state management system executes all of the state templates on the
    # minion to enable more granular control of system state management. The
    # type of template and serialization used for state management needs to be
    # configured on the minion, the default renderer is yaml_jinja. This is a
    # yaml file rendered from a jinja template, the available options are:
    #   yaml_jinja
    #   yaml_mako
    #   yaml_wempy
    #   json_jinja
    #   json_mako
    #   json_wempy
    # ──────────────────────────────────────────────────────────────────────────
    renderer: yaml_jinja
    
    # ──────────────────────────────────────────────────────────────────────────
    # The failhard option tells the minions to stop immediately after the first
    # failure detected in the state execution. Defaults to False.
    # ──────────────────────────────────────────────────────────────────────────
    failhard: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # autoload_dynamic_modules turns on automatic loading of modules found in
    # the environments on the master. This is turned on by default. To turn of
    # autoloading modules when states run, set this value to False.
    # ──────────────────────────────────────────────────────────────────────────
    autoload_dynamic_modules: True
    
    # ──────────────────────────────────────────────────────────────────────────
    # clean_dynamic_modules keeps the dynamic modules on the minion in sync with
    # the dynamic modules on the master, this means that if a dynamic module is
    # not on the master it will be deleted from the minion. By default, this is
    # enabled and can be disabled by changing this value to False.
    # ──────────────────────────────────────────────────────────────────────────
    clean_dynamic_modules: True
    
    # ──────────────────────────────────────────────────────────────────────────
    # If using the local file directory, then the state top file name needs to
    # be defined, by default this is top.sls.
    # ──────────────────────────────────────────────────────────────────────────
    state_top: top.sls
    
    # ──────────────────────────────────────────────────────────────────────────
    # Run states when the minion daemon starts. To enable, set startup_states
    # to:
    #   'highstate' -- Execute state.highstate
    #   'sls' -- Read in the sls_list option and execute the named sls files
    #   'top' -- Read top_file option and execute based on that file on the
    #            Master
    # ──────────────────────────────────────────────────────────────────────────
    startup_states: ''
    
    # ──────────────────────────────────────────────────────────────────────────
    # List of states to run when the minion starts up if startup_states is
    # 'sls':
    #  sls_list:
    #    - edit.vim
    #    - hyper
    # ──────────────────────────────────────────────────────────────────────────
    #sls_list: []
    
    # ──────────────────────────────────────────────────────────────────────────
    # Top file to execute if startup_states is 'top':
    # ──────────────────────────────────────────────────────────────────────────
    #top_file: ''
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                            THREAD SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ──────────────────────────────────────────────────────────────────────────
    # Disable multiprocessing support, by default when a minion receives a
    # publication a new process is spawned and the command is executed therein.
    # ──────────────────────────────────────────────────────────────────────────
    multiprocessing: True
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    #                             UPDATE SETTINGS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Using the features in Esky, a salt minion can both run as a frozen app and
    # be updated on the fly. These options control how the update process
    # (saltutil.update()) behaves.
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ──────────────────────────────────────────────────────────────────────────
    # The url for finding and downloading updates. Disabled by default.
    # ──────────────────────────────────────────────────────────────────────────
    #update_url: False
    
    # ──────────────────────────────────────────────────────────────────────────
    # The list of services to restart after a successful update. Empty by default.
    # ──────────────────────────────────────────────────────────────────────────
    #update_restart_services: []
