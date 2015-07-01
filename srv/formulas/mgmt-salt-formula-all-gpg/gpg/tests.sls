#!yamlscript
#
# vim: set syntax=yaml ts=2 sw=2 sts=2 et :

##
# gpg module and renderer tests
#
# qubesctl state.sls gpg.tests
##


$python: |
    tests = [
        'debug-mode',
        'gpg-import_key',
        'gpg-verify',
        'gpg-renderer',
    ]

#===============================================================================
# Set salt state result debug mode (enable/disable)                   debug-mode
#===============================================================================
$if 'debug-mode' in tests:
  gpg-test-debug-mode-id:
    debug.mode:
      - enable-all: true
      # enable: [qvm.absent, qvm.start]
      # disable: [qvm.absent]
      # disable-all: true

#===============================================================================
# Test new state and module to import gpg key                     gpg-import_key
#
# (moved to salt/gnupg.sls)
#===============================================================================
$if 'gpg-import_key' in tests:
  gpg-import_key-id:
    gpg.import_key:
      # source: /srv/pillar/base/gnupg/keys/nrgaway-qubes-signing-key.asc
      - source: pillar://gnupg/keys/nrgaway-qubes-signing-key.asc
      # contents-pillar: gnupg-nrgaway-key
      # user: salt

#===============================================================================
# Test new state and module to verify detached signed file            gpg-verify
#===============================================================================
$if 'gpg-verify' in tests:
  gpg-verify-id:
    gpg.verify:
      # source: salt://gpg/test-gpg-renderer.sls.asc@dom0
      - source: salt://gpg/test-gpg-renderer.sls.asc
      # key-data: salt://gpg/test-gpg-renderer.sls@dom0
      # user: salt
      # require:
      # - pkg: gnupg

#===============================================================================
# Test gpgrenderer that automatically verifies signed state         gpg-renderer
# state files (vim/init.sls{.asc} is the test file for this)
#===============================================================================
$if 'gpg-renderer' in tests:
  $include: gpg.test-gpg-renderer

