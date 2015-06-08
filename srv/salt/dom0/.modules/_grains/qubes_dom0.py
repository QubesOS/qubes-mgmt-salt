# -*- coding: utf-8 -*-

import salt.config
import salt.grains.core

__opts__ = salt.config.minion_config('/etc/salt/minion')
salt.grains.core.__opts__ = __opts__


def qubes_dom0():
    '''
    Redefine qubes grains.
    '''
    grains = {}
    if salt.grains.core.os_data()['os'] == 'Qubes': 
        grains = {}
        grains['virtual'] = 'Qubes'
        grains['os'] = 'Fedora'
        grains['os_family'] = 'RedHat'
    return grains

