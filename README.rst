This README is not complete and is work-in-progress...
======================================================

In order to utilize the Qubes Management features (`app-salt-config`) two packages
first need to be installed in either Dom0 and/or the AppVM.  Install `salt` version
2014.7.2 or greater, then `qubes-salt-config` or have them baked into the template
by including the `+app-salt-config` flavor when building.

`qubesctl` is inter-changable and an alias for `salt-call --local`


Initial Installation and Setup
------------------------------
1) Intial Setup: sync any modules, etc
       qubesctl saltutil.sync_all

2) Initial Key Import:
       qubesctl state.sls salt.gnupg

3) Highstate will execute all states
       qubesctl state.highstate

4) Highstate test mode only.  Note note all states seem to conform to test
   mode and may apply state anyway.  Needs more testing to confirm or not!
       qubesctl state.highstate test=True


Where are all the configuration files?
--------------------------------------
All the qubes based configuration files are located in `/srv/qubes-*` directories.
The salt minion configuration files are located in `/etc/salt'.

`/srv/qubes-salt/top.sls` contains all the states that will execute when running 
a highstate


To install or remove qubesbuilder policy only as its nto included in the highstate
----------------------------------------------------------------------------------
qubesctl state.sls policy-qubesbuilder.absent
qubesctl state.sls policy-qubesbuilder.absent
