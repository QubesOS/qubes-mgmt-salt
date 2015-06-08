__author__ = 'Jason Mehring'

#
# This module is only used with WingIDE debugger for testing code within
# The debugging environment
#

import sys

from subprocess import call
from salt.scripts import salt_call

SYNC = False

if __name__ == '__main__':
    argv = sys.argv

    # Sync renderers first
    if SYNC:
        call(["salt", "*", "saltutil.sync_all"])

    salt_call()
