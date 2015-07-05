# Set VM type (dom0 or vm)
{% if grains['virtual']|lower == 'qubes' %}
  {% set vmtype = 'dom0' %}
{% else %}
  {% set vmtype = 'vm' %}
{% endif %}

salt:
  clean_config_d_dir: False
  install_packages: True

  # salt master config
  minion:
    # XXX: Missing from salt-formula
    #    fileserver_backend:
    #      - roots
    #      - git

    {% if vmtype == 'vm' %}
    gitfs_provider: dulwich
    # gitfs_remotes: []
    {% endif %}

    file_client: local
    file_roots:
      user:
        - /srv/user_salt
      base:
        - /srv/salt
    fileserver_limit_traversal: False
    hash_type: md5

    pillar_roots:
      user:
        - /srv/user_pillar
      base:
        - /srv/pillar
        - /srv/pillar/base
        - /srv/formulas/gpg-formula/pillar/base
      all:
        - /srv/pillar/all

      # dom0 pillars
      {% if vmtype == 'dom0' %}
      dom0:
        - /srv/pillar/dom0
        - /srv/formulas/virtual-machines-formula/pillar/dom0
      {% endif %}

      # VM pillars
      {% if vmtype == 'vm' %}
      vm:
        - /srv/pillar/vm
      {% endif %}

    # Double quote log stings to prevent parser errors
    log_file: /var/log/salt/minion
    key_logfile: /var/log/salt/key
    log_level: warning
    log_level_logfile: warning
    log_datefmt: '"%H:%M:%S"'
    log_datefmt_logfile: '"%Y-%m-%d %H:%M:%S"'
    log_fmt_console: '"[%(levelname)-8s] %(message)s"'
    log_fmt_logfile: '"%(asctime)s,%(msecs)03.0f [%(name)-17s][%(levelname)-8s] %(message)s"'

    #module_dirs: []
    #returner_dirs: []
    #states_dirs: []
    #render_dirs: []
    #utils_dirs: []
    #providers:
    #  pkg: qubes-dom0-pkg`

    # TODO: Disable unwanted modules
    {% if vmtype == 'dom0' %}
    disable_modules:
      - git
    {% endif %}

    ## XXX: Missing from salt-formula
    ##      Included in:
    ##        /etc/salt/minion.d/nodegroups.conf
    #    nodegroups:
    #      dom0: 'G@virtual:Qubes'
    #      vm: 'P@virtual_subtype:Xen\sPV\sDomU'

    ## XXX: Missing from salt-formula
    ##      Included in:
    ##        /etc/salt/minion.d/reactor.conf
    #    reactor:
    #      - 'minion_start':
    #        - /srv/reactor/sync_all.sls
    #        - /srv/reactor/import_keys.sls

    open_mode: False
    permissive_pki_access: False
    state_verbose: True
    state_output: full
    state_output_diff: False
    #master_finger: ''

    renderer: yaml_jinja
    failhard: False
    autoload_dynamic_modules: True
    clean_dynamic_modules: True
    state_top: top.sls
    startup_states: ''
    #sls_list:
    #  - edit.vim
    #  - hyper
    #top_file: ''

    multiprocessing: True

salt_formulas:
  git_opts:
    # The Git options can be customized differently for each
    # environment, if an option is missing in a given environment, the
    # value from "default" is used instead.
    user:
      # URL where the formulas git repositories are downloaded from
      # it will be suffixed with <formula-name>.git
      baseurl: https://github.com/saltstack-formulas
      # Directory where Git repositories are downloaded
      basedir: /srv/user_formulas
      # Update the git repository to the latest version (False by default)
      update: False
      # Options passed directly to the git.latest state
      options:
        rev: master
    base:
      basedir: /srv/formulas/base
      update: False
    dom0:
      basedir: /srv/formulas/dom0
      update: False
    vm:
      basedir: /srv/formulas/vm
      update: False
    all:
      basedir: /srv/formulas/all
      update: False

  # Options of the file.directory state that creates the directory where
  # the git repositories of the formulas are stored
  basedir_opts:
    makedirs: True
    user: root
    group: root
    mode: 750

  # List of formulas to enable in each environment
  list:
    base:
      - qubes-base
      - qubes-overrides
      - salt-formula
      - yamlscript-formula
      - users-yamlscript-formula
      - gpg-formula

    # dom0 formulas
    {% if vmtype == 'dom0' %}
    dom0:
      - dom0-qvm-formula
      - dom0-update-formula
      - virtual-machines-formula
      - policy-qubesbuilder-formula
      - fix-permissions-formula
      - template-upgrade-formula
    {% endif %}

    # VM formulas
    {% if vmtype == 'vm' %}
    vm:
      - python-pip-formula

    all:
      - vim-formula
      - theme-formula
      - privacy-formula
    {% endif %}

    user:
      # Formulas to set up http://docs.saltstack.com
      - salt-docs-formula

      # This formula ensures that a sysctl parameter is present on the system
      # from a pillar file.
      - sysctl-formula

      # A formula to install and configure rsync as daemon process.
      - rsyncd-formula

      # This formula installs and configures system locales.
      - locale-formula

      # Formula to configure timezone.
      - timezone-formula

      # Mopidy plays music from local disk, Spotify, SoundCloud, Google Play
      # Music, and more. 
      - mopidy-formula

      # Sensu: A monitoring framework that aims to be simple, malleable, and
      # scalable.
      - sensu-formula

      # This module manages your firewall using iptables with pillar configured
      # rules. Thanks to the nature of Pillars it is possible to write global
      # and local settings (e.g. enable globally, configure locally)
      - iptables-formula

      # A networking formula for debian style distributions 
      {% if grains['os_family']|lower == 'debian' %}
      - network-debian-formula 
      {% endif %}

      # os-hardening formula currently supported for Ubuntu.
      {% if grains['os']|lower == 'ubuntu' %}
      - os-hardening-formula
      {% endif %}

      # Flexible provisioning for JDK and JRE tarballs 
      - sun-java-formula

      # Mumble is an open source, low-latency, high quality voice chat software
      # primarily intended for use while gaming.
      - mumble-server-formula

      # Use pillar and scheduler to backup something, anything to the cloud.
      - backuptocloud-formula

      # Tinyproxy is a HTTP proxy server daemon for POSIX operating systems.
      # Designed to be fast and small, it is useful when an HTTP/HTTPS proxy is
      # required, but the system resources for a larger proxy are unavailable.
      - tinyproxy-formula

      # Samba is a free software re-implementation of the SMB/CIFS networking
      # protocol.
      - samba-formula

      # Required for various Debian packages 
      {% if grains['os_family']|lower == 'debian' %}
      - build-essential-formula
      {% endif %}

      # Installs screen, as well as a default .screenrc to
      # /usr/local/etc/.screenrc. The .screenrc included is just an example.
      - screen-formula
