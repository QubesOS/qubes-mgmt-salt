#!/bin/bash -e
# vim: set ts=4 sw=4 sts=4 et :

source "${SCRIPTSDIR}/vars.sh"
source "${SCRIPTSDIR}/distribution.sh"

#### '----------------------------------------------------------------------
info ' Trap ERR and EXIT signals and cleanup (umount)'
#### '----------------------------------------------------------------------
trap cleanup ERR
trap cleanup EXIT

#### '----------------------------------------------------------------------
info ' Installing init-system-helpers'
#### '----------------------------------------------------------------------
DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true \
    chroot apt-get ${APT_GET_OPTIONS} -t wheezy-backports install python-requests python-zmq

#### '-------------------------------------------------------------------------
info ' Installing Qubes Salt Management Flavor'
#### '-------------------------------------------------------------------------
aptInstall salt-common salt-minion qubes-mgmt-salt-vm

#### '----------------------------------------------------------------------
info ' Cleanup'
#### '----------------------------------------------------------------------
trap - ERR EXIT
trap
