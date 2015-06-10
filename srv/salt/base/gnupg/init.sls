# vim: set syntax=yaml ts=2 sw=2 sts=2 et :
#
# Initially, everything will break without a public key being set
#
# Run this to set the key before highstate:
# qubesctl state.sls gnupg

gnupg:
  pkg.installed:
    - order: 1
    - names:
      - python-gnupg
  gpg.import_key:
    - order: 1
    - source: /srv/pillar/gnupg/keys/nrgaway-qubes-signing-key.asc
    # contents-pillar: gnupg-nrgaway-key

