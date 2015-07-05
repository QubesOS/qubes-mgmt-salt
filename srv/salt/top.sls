# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# 1) Intial Setup: sync any modules, etc
# --> qubesctl saltutil.sync_all
#
# 2) Initial Key Import:
# --> qubesctl state.sls gpg
#
# 3) Highstate will execute all states
# --> qubesctl state.highstate
#
# 4) Highstate test mode only.  Note note all states seem to conform to test
#    mode and may apply state anyway.  Needs more testing to confirm or not!
# --> qubesctl state.highstate test=True

# === Base States =============================================================
base:
  '*':
    # --- salt configurations ---
    - salt.standalone
    - salt.directories
    - salt.pkgrepo

    # --- install user salt directories and sample locale states ---
    - salt-user

  # === Base States Formulas ==================================================
    # --- configurations ---
    - gpg
    # users

    # --- tests ---
    # gpg.tests

  # VM nodegroup + enable_gitfs == true
  # Enable in /srv/pillar/vm/salt/formulas.sls
  'P@virtual_subtype:Xen\sPV\sDomU and I@enable_gitfs:true':
    - match: compound
    # --- salt git formulas ---
    {% if grains['os_family']|lower == 'debian' %}
    - salt.gitfs.dulwich
    {% endif %}
    - salt.formulas

# === Common State Formulas ===================================================
all:
  '*':
    # --- applications ---
    - vim

  vm:
    - match: nodegroup
    # --- configurations ---
    - theme
    - theme.fonts_ubuntu
    - theme.fonts_source_code_pro

  # Enable in /srv/pillar/all/privacy/init.sls
  'enable_privacy:true':
    - match: pillar
    # --- configurations ---
    - privacy

# === Dom0 State Formulas =====================================================
dom0:
  dom0:
    - match: nodegroup
    # --- applications ---

    # --- configurations ---
    - virtual-machines

    # --- tests ---
    # qvm.tests
    # qubes-dom0-update.tests

# === AppVM State Formulas ====================================================
vm:
  vm:
    - match: nodegroup
    # --- applications ---
    - python_pip
