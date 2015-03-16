# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# 1) Intial Setup: sync any modules, etc
# --> salt-call --local saltutil.sync_all
#
# 2) Initial Key Import:
# --> salt-call --local state.sls salt.gnupg
#
# 3) Highstate will execute all states
# --> salt-call --local state.highstate
#
# 4) Highstate test mode only.  Note note all states seem to conform to test
#    mode and may apply state anyway.  Needs more testing to confirm or not!
# --> salt-call --local state.highstate test=True

base:
  # === Common ================================================================
  '*':
    # --- salt applications ---
    - salt
    - salt.gnupg
    - salt.minion_absent
    - salt.master_absent
    - salt.api_absent
    - salt.syndic_absent
    - salt.halite_absent

    # --- system configurations ---
    - users

    # --- utilities ---
    - vim

  # === Dom0 ==================================================================
  'virtual:Qubes':
    - match: grain

    # --- salt applications ---

    # --- dom0 configurations ---
    - tests

  # === DomU ==================================================================
  'virtual_subtype:Xen PV DomU':
    - match: grain

    # --- salt applications ---
    - python_pip  # Not needed if salt installed via repo (yum, apt-get)

    # --- appearance ---
    - theme
    - theme.fonts_ubuntu
    - theme.fonts_source_code_pro

dev:
  # === Common ================================================================
  '*': []
