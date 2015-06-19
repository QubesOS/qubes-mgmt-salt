# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:platform:      all

===========================
Qubes test modules for salt
===========================
'''

# Import python libs
import argparse
import logging

from inspect import getargvalues, stack

# Salt + Qubes libs
import module_utils

from qubes_utils import function_alias as _function_alias
from module_utils import ModuleBase as _ModuleBase

# Enable logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'test'


def __virtual__():
    '''
    Confine this module to Qubes dom0 based systems
    '''
    return True

#__outputter__ = {
#    'get_prefs': 'txt',
#}


class _TestBase(_ModuleBase):
    '''Overrides.
    '''
    def __init__(self, *varargs, **kwargs):
        '''
        '''
        frame = stack()[1][0]
        self.__info__ = getargvalues(frame)._asdict()

        if not hasattr(module_utils, '__opts__'):
            module_utils.__opts__ = __opts__
        if not hasattr(module_utils, '__salt__'):
            module_utils.__salt__ = __salt__

        super(_TestBase, self).__init__(*varargs, **kwargs)


@_function_alias('debug')
class _Debug(_TestBase):
    '''
    Sets debug mode for all or specific states status:

    Pass module names to enable or disable.

    Valid actions:

    .. code-block:: yaml

        # Optional
        - enable-all:           [True]
        - disable-all:          [True]
        - enable:               [MODULE ...]
        - disable:              [MODULE ...]
    '''
    def __init__(self, *varargs, **kwargs):
        '''
        '''
        self.arg_options_create(argv_ordering=['flags', 'args', 'varargs', 'keywords'])
        super(_Debug, self).__init__(*varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # Defaults override
        parser.add_argument('--status-mode', nargs='*', default=['all'], choices=('last', 'all', 'debug', 'debug-changes'), help=argparse.SUPPRESS)

        # Optional Positional
        parser.add_argument('id', nargs='?', help=argparse.SUPPRESS)

        # Optional
        parser.add_argument('--enable-all', nargs='?', type=bool, default=False, help='Enable debug mode for all modules')
        parser.add_argument('--disable-all', nargs='?', type=bool, default=False, help='Disable debug mode for all modules')

        parser.add_argument('--enable', nargs='+', default=False, help='Enable debug mode for provided modules')
        parser.add_argument('--disable', nargs='+', default=False, help='Disable debug mode for provided modules')

    def __call__(self):
        args = self.args

        # Enable
        if args.enable_all:
            if '__all__' not in self._debug_mode:
                self._debug_mode.append('__all__')
                self.save_status(message='Enabled \'ALL\'')
            else:
                self.save_status(prefix='[SKIP] ', message='Already enabled \'ALL\'')
        elif args.enable:
            for module in args.enable:
                if module not in self._debug_mode:
                    self._debug_mode.append(module)
                    self.save_status(message='Enabled \'{0}\''.format(module))
                else:
                    self.save_status(prefix='[SKIP] ', message='Already enabled \'{0}\''.format(module))

        # Disable
        if args.disable_all:
            for module in sorted(self._debug_mode, reverse=True):
                self._debug_mode.remove(module)
                self.save_status(message='Disabled \'{0}\''.format(module))
        elif args.disable:
            for module in args.disable:
                if module in self._debug_mode:
                    self._debug_mode.remove(module)
                    self.save_status(message='Disabled \'{0}\''.format(module))
                else:
                    self.save_status(prefix='[SKIP] ', message='Already disabled \'{0}\''.format(module))

        # Returns the status 'data' dictionary
        return self.status()
