# -*- coding: utf-8 -*-
'''
:maintainer:    Jason Mehring <nrgaway@gmail.com>
:maturity:      new
:depends:       python-gpg
:platform:      all

Implementation of gpg utilities
===============================

.. code-block:: yaml

    vim.sls.asc:
      gpg.verify
        - source: salt://vim/init.sls.asc
'''

# Import python libs
import logging

log = logging.getLogger(__name__)


def __virtual__():
    '''
    Only make these states available if a qvm provider has been detected or
    assigned for this minion
    '''
    return 'gpg.verify' in __salt__

def import_key(name,
          source,
          homedir=None,
          **kwargs
        ):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    result = __salt__['gpg.import_key'](source, homedir)
    ret['comment'] = result['comment']

    if not result['fingerprint']:
        ret['result'] =  False
        return ret

    ret['result'] = True
    return ret


def verify(name,
          source,
          data_source=None,
          homedir=None,
          **kwargs
        ):
    '''
    '''
    ret = {'name': name,
           'changes': {},
           'result': False,
           'comment': ''}

    result = __salt__['gpg.verify'](source, data_source, homedir)
    ret['comment'] = result.status

    if not result.valid:
        ret['result'] =  False
        return ret
    ret['result'] = True
    return ret
