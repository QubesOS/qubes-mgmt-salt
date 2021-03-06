#!/bin/bash -e
# vim: set ts=4 sw=4 sts=4 et :

source "${SCRIPTSDIR}/vars.sh"
source "${SCRIPTSDIR}/distribution.sh"

#### '----------------------------------------------------------------------
info ' Trap ERR and EXIT signals and cleanup (umount)'
#### '----------------------------------------------------------------------
trap cleanup ERR
trap cleanup EXIT

#### '-------------------------------------------------------------------------
info ' Installing Saltstack Repo'
#### '-------------------------------------------------------------------------
saltkey="$(dirname "${0}")/keys/jessie-saltstack-gpg-key.pub"
cat "${saltkey}" | chroot apt-key add -
    
list="${INSTALLDIR}/etc/apt/sources.list.d/saltstack.list"
touch "${list}"
source="deb http://repo.saltstack.com/apt/debian/8/amd64/latest ${DEBIANVERSION} main"
if ! grep -r -q "$source" "${list}"*; then
    echo -e "$source" >> "${list}"
fi
aptUpdate

#### '-------------------------------------------------------------------------
info ' Installing Qubes Salt Management Flavor'
#### '-------------------------------------------------------------------------
aptInstall salt-common salt-minion qubes-mgmt-salt-vm

#### '----------------------------------------------------------------------
info ' Cleanup'
#### '----------------------------------------------------------------------
trap - ERR EXIT
trap
