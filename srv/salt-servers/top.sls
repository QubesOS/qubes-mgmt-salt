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
  '*':
    # --- salt applications ---
