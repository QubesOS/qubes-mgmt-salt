# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# 1) Intial Setup: sync any modules, etc
# --> qubesctl saltutil.sync_all
#
# 2) Initial Key Import:
# --> qubesctl state.sls gnupg
#
# 3) Highstate will execute all states
# --> qubesctl state.highstate
#
# 4) Highstate test mode only.  Note note all states seem to conform to test
#    mode and may apply state anyway.  Needs more testing to confirm or not!
# --> qubesctl state.highstate test=True

base:
  # === Base States ===========================================================
  '*':
    # --- salt configurations ---
    - salt
    - salt.minion_absent
    - salt.master_absent
    - salt.api_absent
    - salt.syndic_absent
    - salt.halite_absent

    # --- install user salt directories and sample locale states ---
    - salt-user

  # === Base States Formulas ==================================================
    # --- applications ---
    - vim

    # --- configurations ---
    - gpg
    # users

    # --- tests ---
    # gpg.tests

dom0:
  # === Dom0 State Formulas ===================================================
  'virtual:Qubes':
    - match: grain
    # --- applications ---

    # --- configurations ---
    - virtual-machines

    # --- tests ---
    # qvm.tests
    # qubes-dom0-update.tests

vm:
  # === AppVM State Formulas ==================================================
  'virtual_subtype:Xen PV DomU':
    - match: grain

    # --- applications ---
    - python_pip  # Not needed if salt installed via repo (yum, apt-get)

    # --- configurations ---
    - theme
    - theme.fonts_ubuntu
    - theme.fonts_source_code_pro

vm_other:
  # === Other State Formulas ==================================================
  'vm_other:true':
    - match: pillar
    # --- applications ---

    # --- configurations ---
    - os
