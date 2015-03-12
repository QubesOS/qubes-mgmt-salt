# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

# Test qubes-dom0-update
git:
  pkg.installed:
    - name: git

#salt-testvm:
#  qvm.create:
#    - template: fedora-20-x64
#    - label: red
#    - mem: 3000
#    - vcpus: 4

#salt-testvm-remove:
#  qvm.remove:
#    - name: salt-testvm

#fedora-20-x64:
#  qvm.clone:
#    - target: fedora-clone
#fedora-clone:
#  qvm.remove: []

# Test prefs
#fc21:
#  qvm.prefs:
#    # label: oranges  # Deliberate error
#    - label: orange
#    - template: debian-jessie
#    - memory: 400
#    - maxmem: 4000
#    - include_in_backups: False
#  qvm.check: []

fc21-prefs:
  qvm.prefs:
    - name: fc21
    - label: green
    - template: debian-jessie
    - memory: 400
    - maxmem: 4000
    - include_in_backups: True

fc21-check:
  qvm.check:
    - name: fc21

fc211-missing:
  qvm.missing:
    - name: fc211

#fc21-running:
#  qvm.running:
#    - name: fc21

fc21-dead:
  qvm.dead:
    - name: fc21

# Deliberate Fail
#fc211-running:
#  qvm.running:
#    - name: fc211

netvm-running:
  qvm.running:
    - name: netvm

fc21-service-test:
  qvm.service:
    - name: fc21
    - enable:
      - test
      - another_test
    - disable: meminfo-writer

fc21-start:
  qvm.start:
    - name: fc21
    # options:
    # - tray
    # - no-guid
    # - dvm
    # - debug
    # - install-windows-tools
    # - drive: DRIVE
    # - hddisk: DRIVE_HD
    # - cdrom: DRIVE_CDROM
    # - custom-config: CUSTOM_CONFIG

# Test new state and module to verify detached signed file
#test-file:
#  gpg.verify:
#    - source: salt://vim/init.sls.asc
#    # homedir: /etc/salt/gpgkeys
#    - require:
#      - pkg: gnupg

# Test new state and module to import gpg key
# (moved to salt/gnupg.sls)
#nrgaway_key:
#  gpg.import_key:
#    - source: salt://dom0/nrgaway-qubes-signing-key.asc
#    # homedir: /etc/salt/gpgkeys

# Test new renderer that automatically verifies signed state files
# (vim/init.sls{.asc} is the test file for this)
