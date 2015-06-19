# -*- coding: utf-8 -*-
'''
gnupg related utilities
'''

# Import python libs
import os
import argparse
import logging

from inspect import getargvalues, stack

import salt.utils
import salt.modules.gpg as _gpg
from salt.exceptions import (
    CommandExecutionError, SaltInvocationError
)

# Salt + Qubes libs
import module_utils
from qubes_utils import Status
from qubes_utils import function_alias as _function_alias
from qubes_utils import tostring as _tostring
from module_utils import ModuleBase as _ModuleBase

# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'gpg'


def __virtual__():
    '''
    Confine this module to gpg enabled systems
    '''
    if _gpg.__virtual__:
        return __virtualname__
    return False


class _GPGBase(_ModuleBase):
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

        super(_GPGBase, self).__init__(*varargs, **kwargs)


def _get_path(filename, pillar=False):
    if not filename:
        return ''

    saltenv = 'base'
    if filename.startswith('pillar://'):
        pillar = True
        filename = filename.replace('pillar://', 'salt://')

    if filename.startswith('salt://'):
        try:
            filename, saltenv = filename.split('@')
        except ValueError: pass

    client = salt.fileclient.get_file_client(__opts__, pillar)
    if pillar:
        file_roots = client.opts['file_roots']
        client.opts['file_roots'] = client.opts['pillar_roots']

    filename = client.cache_file(filename, saltenv)
    if pillar:
        client.opts['file_roots'] = file_roots

    if not filename or not os.path.exists(filename):
        filename = ''
    return filename


def _get_data(filename):
    try:
        with open(filename) as file_:
            return file_.read()
    except IOError, error:
        raise CommandExecutionError('Error reading: {0}. {1}'.format(filename,  error))


@_function_alias('import_key')
class _Import_key(_GPGBase):
    '''
    Import a key from text or file

    user
        Which user's keychain to access, defaults to user Salt is running as.
        Passing the user as 'salt' will set the GPG home directory to
        /etc/salt/gpgkeys.

    contents
        The text containing import key to import.

    contents-pillar
        The pillar id containing import key to import.

    source
        The filename containing the key to import.

    CLI Example:

    .. code-block:: bash

        qubesctl gpg.import_key contents='-----BEGIN PGP PUBLIC KEY BLOCK-----
        ... -----END PGP PUBLIC KEY BLOCK-----'

        qubesctl gpg.import_key source='/path/to/public-key-file'

        qubesctl gpg.import_key contents-piller='gpg:gpgkeys'
    '''
    def __init__(self, *varargs, **kwargs):
        '''
        '''
        super(_Import_key, self).__init__(*varargs, **kwargs)
        self.args.contents_pillar = _tostring(self.args.contents_pillar) if self.args.contents_pillar else self.args.contents_pillar

    @classmethod
    def parser_arguments(cls, parser):
        # 'name'
        parser.add_argument('name', nargs='?', help=argparse.SUPPRESS)
        #    help='The name id of state object')

        # Mutually exclusive group (source, contents, contents-pillar)
        group = parser.add_mutually_exclusive_group()

        # 'source'
        group.add_argument('source', nargs='?',
            help='The filename containing the key to import')

        # 'contents'
        group.add_argument('--contents', nargs=1, metavar='TEXT',
            help='The text containing import key to import')

        # 'contents-pillar' + 'contents_pillar'
        group.add_argument('--contents-pillar', '--contents_pillar', type=_tostring, nargs=1, metavar='PILLAR-ID',
            help='The pillar id containing import key to import')

        # 'user'
        parser.add_argument('--user', nargs=1, default='salt',
            help="Which user's keychain to access, defaults to user Salt is \
            running as.  Passing the user as 'salt' will set the GPG home \
            directory to /etc/salt/gpgkeys.")

    def import_key(self, user=None, text=None, filename=None):
        '''
        salt.module.gpg.import_key is broken, so implement it here for now
        '''
        ret = {
           'result': False,
           'message': 'Unable to import key.'
         }

        gnupg = _gpg._create_gpg(user)

        if not text and not filename:
            raise SaltInvocationError('filename or text must be passed.')

        if filename:
            try:
                with salt.utils.flopen(filename, 'rb') as _fp:
                    lines = _fp.readlines()
                    text = ''.join(lines)
            except IOError:
                raise SaltInvocationError('filename does not exist.')

        imported_data = gnupg.import_keys(text)
        log.debug('imported_data {0}'.format(imported_data.__dict__.keys()))
        log.debug('imported_data {0}'.format(imported_data.counts))

        results = imported_data.results[-1]
        if results.get('fingerprint', None) and 'ok' in results:
            ret['result'] = True

        ret['message'] = results.get('text', imported_data.summary())
        ret['stdout'] = imported_data.stderr
        return ret

    def __call__(self):
        args = self.args
        keywords = {'user': args.user,}

        status = Status()
        if args.source:
            keywords['filename'] = _get_path(args.source)
            if not keywords['filename']:
                status.recode = 1
                status.message = 'Invalid filename source {0}'.format(args.source)
        elif args.contents:
            keywords['text'] = args.contents
        elif args.contents_pillar:
            keywords['text'] = __pillar__.get(args.contents_pillar, None)
            if not keywords['text']:
                status.recode = 1
                status.message = 'Invalid pillar id source {0}'.format(args.contents_pillar)
        else:
            status.recode = 1
            status.message = 'Invalid options!'

        if status.failed():
            self.save_status(status)
        if __opts__['test']:
            self.save_status(message='Key will be imported')
        else:
            status = Status(**self.import_key(**keywords))
            self.save_status(status)

        # Returns the status 'data' dictionary
        return self.status()


@_function_alias('verify')
class _Verify(_GPGBase):
    '''
    Verify a message or file

    source
        The filename.asc to verify.

    key-content
        The text to verify.

    data-source
        The filename data to verify.

    user
        Which user's keychain to access, defaults to user Salt is running as.
        Passing the user as 'salt' will set the GPG home directory to
        /etc/salt/gpgkeys.

    CLI Example:

    .. code-block:: bash

        qubesctl gpg.verify source='/path/to/important.file.asc'

        qubesctl gpg.verify <source|key-content> [key-data] [user=]

    '''
    def __init__(self, name, *varargs, **kwargs):
        '''
        '''
        super(_Verify, self).__init__(name, *varargs, **kwargs)

    @classmethod
    def parser_arguments(cls, parser):
        # 'name'
        parser.add_argument('name',
            help='The name id of state object')

        # Mutually exclusive group (source, contents)
        group = parser.add_mutually_exclusive_group()

        # 'source'
        group.add_argument('source', nargs='?',
            help='The filename containing the key to import')

        # 'contents'
        group.add_argument('--key-contents', '--key_contents', nargs=1,
            help='The text containing import key to import')

        # 'data'
        parser.add_argument('--data-source', '--data_source', nargs='?',
            help='Source file data path to verify (source)')

        # 'user'
        parser.add_argument('--user', nargs=1, default='salt',
            help="Which user's keychain to access, defaults to user Salt is \
            running as.  Passing the user as 'salt' will set the GPG home \
            directory to /etc/salt/gpgkeys.")

    def __call__(self):
        args = self.args
        gnupg = _gpg._create_gpg(args.user)

        status = Status()

        # Key source validation
        key_source = None
        if args.source:
            key_source = _get_path(args.source)
            if not key_source:
                status.recode = 1
                status.message = 'GPG validation failed: invalid key-source {0}'.format(key_source)
        elif args.key_contents:
            key_source = args.key_contents
        else:
            key_source = _get_path(args.name)

        # Data source validation
        data_source = _get_path(args.data_source)
        if not data_source:
            data_source, ext = os.path.splitext(key_source)

        if not os.path.exists(data_source):
            status.retcode = 1
            message = 'GPG validation failed: invalid data-source {0}'.format(data_source)
            self.save_status(status, message=message)
            return self.status()

        # GPG verify
        status = Status()
        data = gnupg.verify_data(key_source, _get_data(data_source))

        if not data.valid:
            raise CommandExecutionError(data.stderr)

        status.stdout = data.stderr
        self.save_status(status)

        # Returns the status 'data' dictionary
        return self.status()
