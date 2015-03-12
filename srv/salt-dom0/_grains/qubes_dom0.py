# -*- coding: utf-8 -*-
def qubes_dom0():
    '''
    Redefine qubes grains.
    '''
    grains = {}
    if __salt__['core.os_data']()['os'] == 'Qubes':
        grains = {}
        grains['virtual'] = 'Qubes'
        grains['os'] = 'Fedora'
        grains['os_family'] = 'RedHat'
    return grains

