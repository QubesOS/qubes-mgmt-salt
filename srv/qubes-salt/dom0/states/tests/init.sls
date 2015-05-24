#!yamlscript
#
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# Qubes state, and module tests
#
# Debug Environment:
#   --local state.highstate
#   --local state.highstate -l debug
#   --local state.highstate test=true
#   --local state.single test=true qvm.remove salt-testvm just-db
##


#===============================================================================
#
# CURRENT ISSUES:
# ---------------
# - comments when TEST mode enabled incorrect
# - test with strict as well
#   - NOTE: Addedd manual debug code for strict in state module
#
# - can we merge start, shutdown, kill, pause, unpause into State?
#   - Then just have 'start', etc sub-class --or-- would it become too messy?
#   - maybe state call; would call start(), shutdown()
#   - subparsers or seperate classes?
#   - help doc considerations as well
#
#   - module output is quite verbose.  Need to implement different filters
#     to allow different type of output (for CLI; web interface?)
#
# TEST PROCEDURES
# ----------------
# - All highstate and state test should produce similar output
# - module mode does not have TEST mode
#   - Test init.sls highstate (WingIDE)
#   - Test init.sls highstate (command line)
#   - Test init.sls highstate test=true (WingIDE)
#   - Test init.sls highstate test=true (command line)
#   - Test salt-call-tests - documentation (commandline)
#   - Test salt-call-tests - state mode (commandline)
#   - Test salt-call-tests - state mode TEST=1 (commandline)
#   - Test salt-call-tests - module mode (commandline)
#   + Run all above again with strict mode enabled
#
# TODO:
# -----
# - Complete all individual tests
# - Make sure all individual test have 'all' possible options (can comment out)
# - Complete qvm-all
# - Create non yamlscript test state file with same tests
# - Create a bash script file that will test each qvm-* using commandline
#   salt-call
# - run TEST mode on everything to confirm no states run; only test mode results
#
# - Convert remainder of _modules to classes
# - Research if we can remove code duplication in _states; maybe combine
#   _call_function AND _vm_action for standardized result comments / output
#
# - ONLY when all the above is complete should I consider cleaning codebase
#   as some things may need to be switched around again to allow easy
#   commandline access (IE: service uses varags; not kwargs)
# - Make sure commandline usage goes in modual docstrings
#
#===============================================================================

# Global modes
# ============
# strict:
# -------
# Strict mode toggles how certain states are passed or failed. The following
# table will list the effect of enabled.  Further setting the strict to fail
# will then prevent any further taks within the state id or anything that
# requires it.
#
# Strict mode is mostly useful to confirm  absolute state.
#
# Vaild Actions: [ (false) | true | fail ]
#
#       qvm.kill: Fail on halted, absent
#       qvm.dead: Fail on absent
#     qvm.remove: Fail on absent
#     qvm.absent: Fail on exists
#     qvm.create: Fail on exists
#     qvm.exists: Fail on absent
#      qvm.prefs: No effect
#    qvm.service: No effect
#      qvm.start: Fail on any mode other than halted
#    qvm.running: Fail on any mode other than running
#      qvm.pause: Fail on any mode other than running
#    qvm.unpause: Fail on any mode other that paused
#   qvm.shutdown: Fail on halted, absent
#        qvm.run: Fail on running - Error on pause or transient if 'auto' not set
#      qvm.clone: No effect
#         qvm.vm: All of above, but will abort any futher actions

$python: |
    test_vm_name = 'salt-testvm6'

    tests = [
        'qvm-kill',
        'qvm-dead',
        'qvm-remove',
        'qvm-absent',
        'qvm-create',
        'qvm-exists',
        'qvm-prefs-list',
        'qvm-prefs-get',
        'qvm-prefs',
        'qvm-service',
        'qvm-start',
        'qvm-running',
      # 'qvm-pause',
      # 'qvm-unpause',
      # 'qvm-shutdown',
        'qvm-run',
      # 'qvm-clone',

      # 'qvm-vm',
      # 'qubes-dom0-update',

      # 'fail-qvm-running',
      # 'gpg-verify',
      # 'gpg-import_key',
      # 'gpg-renderer',
    ]


#===============================================================================
# Test qubes-dom0-update                                       qubes-dom0-update
#===============================================================================
$if 'qubes-dom0-update' in tests:
  git:
    pkg.installed:
      - name: git

#===============================================================================
# Kill VM                                                               qvm-kill
#===============================================================================
$if 'qvm-kill' in tests:
  qvm-kill-id:
    qvm.kill:
      - name: $test_vm_name

#===============================================================================
# Confirm VM is dead (halted)                                           qvm-dead
#===============================================================================
$if 'qvm-dead' in tests:
  qvm-dead-id:
    qvm.dead:
      - name: $test_vm_name

#===============================================================================
# Remove VM                                                           qvm-remove
#===============================================================================
$if 'qvm-remove' in tests:
  qvm-remove-id:
    qvm.remove:
      - name: $test_vm_name
      # flags:
        # just-db
        # force-root
        # quiet

#===============================================================================
# Confirm VM does not exist                                           qvm-absent
#===============================================================================
$if 'qvm-absent' in tests:
  qvm-absent-id:
    qvm.absent:
      - name: $test_vm_name
      # flags:
        # quiet

#===============================================================================
# Create VM                                                           qvm-create
#===============================================================================
$if 'qvm-create' in tests:
  qvm-create-id:
    qvm.create:
      - name: $test_vm_name
      - template: fedora-21
      - label: red
      - mem: 3000
      - vcpus: 4
      # root-move-from: </path/xxx>
      # root-copy-from: </path/xxx>
      - flags:
        - proxy
        # hvm
        # hvm-template
        # net
        # standalone
        # internal
        # force-root
        # quiet

#===============================================================================
# Confirm vm exists                                                   qvm-exists
#===============================================================================
$if 'qvm-exists' in tests:
  qvm-exists-id:
    qvm.exists:
      - name: $test_vm_name
      # flags:
        # quiet

#===============================================================================
# List VM preferences                                             qvm-prefs-list
#===============================================================================
$if 'qvm-prefs-list' in tests:
  qvm-prefs-list1-id:
    qvm.prefs:
      - name: $test_vm_name
      - action: list
  qvm-prefs-list2-id:
    qvm.prefs:
      - name: $test_vm_name

#===============================================================================
# Get VM preferences                                               qvm-prefs-get
#===============================================================================
$if 'qvm-prefs-get' in tests:
  qvm-prefs-get-id:
    qvm.prefs:
      - name: $test_vm_name
      - action: get
      - label:              green
      - template:           debian-jessie
      - memory:             400
      - maxmem:             4000
      - include-in-backups: false

#===============================================================================
# Modify VM preferences                                                qvm-prefs
#===============================================================================
$if 'qvm-prefs' in tests:
  qvm-prefs-id:
    qvm.prefs:
      - name: $test_vm_name
      - action: set
      - label:              green
      - template:           debian-jessie
      - memory:             400
      - maxmem:             4000
      - include-in-backups: false
      # pcidevs:            ['04:00.0']
      # netvm:              sys-firewall
      # kernel:             default
      # vcpus:              2
      # kernelopts:         nopat iommu=soft swiotlb=8192
      # mac:                auto
      # debug:              true
      # default-user:       tester
      # qrexec-timeout:     120
      # internal:           true
      # autostart:          true
      # flags:
        # force-root
      # The following keys do not seem to exist in Qubes prefs DB
      # drive:              ''
      # timezone:           UTC
      # qrexec-installed:   true
      # guiagent-installed: true
      # seamless-gui-mode:  false

#===============================================================================
# Modify VM services                                                 qvm-service
#===============================================================================
$if 'qvm-service' in tests:
  qvm-service-id:
    qvm.service:
      - name: $test_vm_name
      - enable:
        - test
        - test2
        - another_test
        - another_test2
        - another_test3
      - disable:
        - meminfo-writer
        - test3
        - test4
        - another_test4
        - another_test5
      # default: [string,]
      # list: [string,]

#===============================================================================
# Start VM                                                             qvm-start
#===============================================================================
$if 'qvm-start' in tests:
  qvm-start-id:
    qvm.start:
      - name: $test_vm_name
      # drive: <string>
      # hddisk: <string>
      # cdrom: <string>
      # custom-config: <string>
      # flags:
        # quiet  # *** salt default ***
        # no-guid  # *** salt default ***
        # tray
        # dvm
        # debug
        # install-windows-tools

#===============================================================================
# Confirm VM is running                                              qvm-running
#===============================================================================
$if 'qvm-running' in tests:
  qvm-running-id:
    qvm.running:
      - name: $test_vm_name

#===============================================================================
# Pause VM                                                             qvm-pause
#===============================================================================
$if 'qvm-pause' in tests:
  qvm-pause-id:
    qvm.pause:
      - name: $test_vm_name

#===============================================================================
# Unpause VM                                                         qvm-unpause
#===============================================================================
$if 'qvm-unpause' in tests:
  qvm-unpause-id:
    qvm.unpause:
      - name: $test_vm_name

#===============================================================================
# Shutdown VM                                                       qvm-shutdown
#===============================================================================
$if 'qvm-shutdown' in tests:
  qvm-shutdown-id:
    qvm.shutdown:
      - name: $test_vm_name
      # exclude: [exclude_list,]
      # flags:
        # quiet
        # force
        # wait
        # all
        # kill

#===============================================================================
# Run 'gnome-terminal' in VM                                             qvm-run
#
# TODO: Test auto-start
#===============================================================================
$if 'qvm-run' in tests:
  qvm-run-id:
    qvm.run:
      - name: $test_vm_name
      - cmd: gnome-terminal
      # user: <string>
      # exclude: [sys-net, sys-firewall]
      # localcmd: </dev/null>
      # color-output: 31
      - flags:
        # quiet
        - auto
        # tray
        # all
        # pause
        # unpause
        # pass-io
        # nogui
        # filter-escape-chars
        # no-filter-escape-chars
        # no-color-output

#===============================================================================
# Clone VM                                                             qvm-clone
#===============================================================================
$if 'qvm-clone' in tests:
  qvm-clone-id:
    qvm.clone:
      - name: $test_vm_name
      - target: $'{0}-clone'.format(test_vm_name)
      # path:                 </path/xxx>
      - flags:
        - shutdown
        # quiet
        # force-root

  qvm-clone-remove-id:
    qvm.remove:
      - name: $'{0}-clone'.format(test_vm_name)

#===============================================================================
# Combined states (all qvm-* commands available within one id)           qvm-all
#===============================================================================
$if 'qvm-vm' in tests:
  qvm-vm-id:
    qvm.vm:
      - name: $test_vm_name
      - strict: false
      - actions:
        - kill
        - dead
        - remove
        - absent
        - create
        - exists
        - prefs
        - service
        - start
        - running
        - pause
        - unpause
        - shutdown
        - run
        - clone
      - kill: []
      - dead: []
      - remove: []
        # flags:
          # just-db
          # force-root
          # quiet
      - absent: []
        # flags:
          # quiet
      - create:
        - template: fedora-21
        - label: red
        - mem: 3000
        - vcpus: 4
        # root-move-from: </path/xxx>
        # root-copy-from: </path/xxx>
        - flags:
          - proxy
          # hvm
          # hvm-template
          # net
          # standalone
          # internal
          # force-root
          # quiet
      - exists: []
        # flags:
          # quiet
      - prefs:
        - action: set
        - label: green  # red|yellow|green|blue|purple|orange|gray|black
        - template: debian-jessie
        - memory: 400
        - maxmem: 4000
        - include-in-backups: false  # true|false
        # pcidevs:              [string,]
        # netvm:                <string>
        # kernel:               <string>
        # vcpus:                <int>
        # kernelopts:           <string>
        # mac:                  <string> (auto)
        # debug:                true|(false)
        # default-user:         <string>
        # qrexec-timeout:       <int> (60)
        # internal:             true|(false)
        # autostart:            true|(false)
        # flags:
          # force-root
        # The following keys do not seem to exist in Qubes prefs DB
        # drive:              ''
        # timezone:           UTC
        # qrexec-installed:   true
        # guiagent-installed:  true
        # seamless-gui-mode:  false
      - service:
        - enable:
          - test
          - test2
          - another_test
          - another_test2
          - another_test3
        - disable:
          - meminfo-writer
          - test3
          - test4
          - another_test4
          - another_test5
        # default: [string,]
        # list: [string,]
      - start: []
        # drive: <string>
        # hddisk: <string>
        # cdrom: <string>
        # custom-config: <string>
        # flags:
          # quiet  # *** salt default ***
          # no-guid  # *** salt default ***
          # tray
          # dvm
          # debug
          # install-windows-tools
      - running: []
      - pause: []
      - unpause: []
      - shutdown: []
        # exclude: [exclude_list,]
        # flags:
          # quiet
          # force
          # wait
          # all
          # kill
      - run:
        - cmd: gnome-terminal
        # user: <string>
        # exclude: [sys-net, sys-firewall]
        # localcmd: </dev/null>
        # color-output: 31
        - flags:
          # quiet
          - auto
          # tray
          # all
          # pause
          # unpause
          # pass-io
          # nogui
          # filter-escape-chars
          # no-filter-escape-chars
          # no-color-output

#===============================================================================
# Deliberate Fail                                               FAIL qvm-running
#===============================================================================
$if 'fail-qvm-running' in tests:
  fail-qvm-running-id:
    qvm.vm:
      - name: $test_vm_name
      - shutdown: []
      - running: []

#===============================================================================
# Test new state and module to verify detached signed file            gpg-verify
#===============================================================================
$if 'gpg-verify' in tests:
  gpg-verify-id:
    gpg.verify:
      - source: salt://vim/init.sls.asc
      # homedir: /etc/salt/gpgkeys
      - require:
        - pkg: gnupg

#===============================================================================
# Test new state and module to import gpg key                     gpg-import_key
#
# (moved to salt/gnupg.sls)
#===============================================================================
$if 'gpg-import_key' in tests:
  gpg-import_key-id:
    gpg.import_key:
      - source: salt://dom0/nrgaway-qubes-signing-key.asc
      # homedir: /etc/salt/gpgkeys

#===============================================================================
# Test gpgrenderer that automatically verifies signed state         gpg-renderer
# state files (vim/init.sls{.asc} is the test file for this)
#===============================================================================
#$if 'gpg-renderer' in tests:
#  gpg-renderer-id:
#    pkg.installed:
#      - name: vim

