#!/bin/bash -e
# vim: set ts=4 sw=4 sts=4 et :

echo "--> Installing Qubes Salt Management Flavor"
yum install -c $SCRIPTSDIR/../template-yum.conf $YUM_OPTS -y --installroot=$(pwd)/mnt salt salt-minion qubes-salt-config || RETCODE=1

