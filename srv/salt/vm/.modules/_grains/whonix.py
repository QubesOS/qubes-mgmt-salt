# -*- coding: utf-8 -*-

import salt.config
import salt.grains.core

__opts__ = salt.config.minion_config('/etc/salt/minion')
salt.grains.core.__opts__ = __opts__


def whonix():
    '''
    Redefine whonix grains.
    '''
    grains = {}
    if salt.grains.core.os_data()['os'] == 'Whonix': 
        grains = {}
        grains['virtual'] = 'Qubes+Whonix'
        grains['os'] = 'Debian'
        grains['os_family'] = 'Debian'
    return grains

