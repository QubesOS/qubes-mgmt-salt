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
    # os

    # --- tests ---
    # gpg.tests

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
    - python_pip  # Not needed if salt installed via repo (yum, apt-get)

    # --- configurations ---
    - theme
    - theme.fonts_ubuntu
    - theme.fonts_source_code_pro

# === Other State Formulas ====================================================
vm_other:
  vm_other:
    - match: nodegroup
    # --- applications ---
    # --- configurations ---
    - os
