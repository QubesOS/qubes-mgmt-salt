This README is not complete and is work-in-progress...
======================================================

In order to utilize the Qubes Management features (`qubes-mgmt`) two
packages first need to be installed in either Dom0 and/or the AppVM.  Install
`salt` version 2015.5.0 or greater, then for dom0 `qubes-salt-mgmt-dom0` or
`qubes-mgmt-salt-vm` for an AppVM, or have them built into the template by
including the `+salt` template flavor when building.

`qubesctl` is inter-changeable and an alias for `salt-call --local` and
contains additional code to apply any required patches.


Initial Installation and Setup
------------------------------
1) Initial Setup: sync any modules, etc
       qubesctl saltutil.sync_all

2) Highstate will execute all states
       qubesctl state.highstate

3) Highstate test mode only.  Note note all states seem to conform to test
   mode and may apply state anyway.  Needs more testing to confirm or not!
       qubesctl state.highstate test=True


Where are all the configuration files?
--------------------------------------
All the qubes based configuration files are located in `/srv/*`
directories.  The salt minion configuration files are located in `/etc/salt'.

`/srv/salt/_tops/**` contain all the states that will execute when running a
highstate.

Some Useful Commands
--------------------
qubesctl saltutil.sync_all:

    Sync all modules.  If a problem exists, one may remove the salt cache
    directory (`rm -r /var/cache/salt`) and re-sync the modules

qubesctl top.enable <topname> [saltevn=(base)]:

    Enable / disable states to run with highstate. Example:
        qubesctl top.enable privacy saltenv=all
        qubesctl top.disable vim.salt saltenv=all
        qubesctl top.disable gnupg (no need to enter saltenv for base modules)
        qubesctl top.disable gnupg pillar=true (disable pillar)

qubesctl top.enabled:

    List enabled state files (located within `/srv/salt/_tops**` and
    `/srv/pillar/_tops**`). `top.disabled` to list disabled, not activated
    states

qubesctl state.sls config:

    Re-run configuration (updates `/etc/salt/minion.d/f_defaults.conf`)

Examples of running included formulas
-------------------------------------
qubesctl state.sls policy-qubesbuilder
qubesctl state.sls policy-qubesbuilder.absent
