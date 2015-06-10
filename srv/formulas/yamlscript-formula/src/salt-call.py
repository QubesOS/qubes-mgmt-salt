__author__ = 'Jason Mehring'

#
# This module is only used with WingIDE debugger for testing code within
# The debugging environment
#
# Stage 1: bind /srv/...modules to cache/extmods.  No sync will take place
#          since files are bound

# BIND
#   True  : bind custom modules
#   False : do not bind custom modules, but will attempt umounting then exit
#   None  : do not bind custom modules, and do not attempt umounting
BIND = True

import os
import sys
import shutil
import subprocess
import logging

import salt.config
import salt.fileclient
import salt.fileserver
import salt.loader
import salt.modules.saltutil
import salt.pillar

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

from salt.scripts import salt_call
from salt.modules.saltutil import (
    _get_top_file_envs, _listdir_recursively, _list_emptydirs
)
from salt.ext.six import string_types

# Enable logging
log = logging.getLogger(__name__)

BASE_DIR = os.getcwd()

# Set salt pillar, grains and opts settings so they can be applied to modules
__opts__ = salt.config.minion_config('/etc/salt/minion')
__opts__['grains'] = salt.loader.grains(__opts__)
pillar = salt.pillar.get_pillar(
    __opts__,
    __opts__['grains'],
    __opts__['id'],
    __opts__['environment'],
)
__opts__['pillar'] = pillar.compile_pillar()
__salt__ = salt.loader.minion_mods(__opts__)
__grains__ = __opts__['grains']
__pillar__ = __opts__['pillar']
__context__ = {}

salt.modules.saltutil.__opts__ =  __opts__
salt.modules.saltutil.__grains__ =  __grains__
salt.modules.saltutil.__pillar__ =  __pillar__
salt.modules.saltutil.__salt__ =  __salt__
salt.modules.saltutil.__context__ =  __context__


def _bind(form, saltenv=None, umount=False):
    '''
    Bind the files in salt extmods directory within the given environment
    '''
    if saltenv is None:
        saltenv = _get_top_file_envs()
    if isinstance(saltenv, string_types):
        saltenv = saltenv.split(',')
    ret = []
    remote = set()
    source = os.path.join('salt://_{0}'.format(form))
    mod_dir = os.path.join(__opts__['extension_modules'], '{0}'.format(form))

    if not os.path.isdir(mod_dir):
        log.info('Creating module dir {0!r}'.format(mod_dir))

        try:
            os.makedirs(mod_dir)
        except (IOError, OSError):
            msg = 'Cannot create cache module directory {0}. Check permissions.'
            log.error(msg.format(mod_dir))

    for sub_env in saltenv:
        log.info('Syncing {0} for environment {1!r}'.format(form, sub_env))
        cache = []
        log.info('Loading cache from {0}, for {1})'.format(source, sub_env))

        # Grab only the desired files (.py, .pyx, .so)
        cache.extend(
            __salt__['cp.cache_dir'](
                source, sub_env, include_pat=r'E@\.(pyx?|so)$'
            )
        )
        local_cache_base_dir = os.path.join(
                __opts__['cachedir'],
                'files',
                sub_env
                )
        log.debug('Local cache base dir: {0!r}'.format(local_cache_base_dir))

        local_cache_dir = os.path.join(local_cache_base_dir, '_{0}'.format(form))
        log.debug('Local cache dir: {0!r}'.format(local_cache_dir))

        client = salt.fileclient.get_file_client(__opts__)
        fileserver = salt.fileserver.Fileserver(__opts__)

        for fn_ in cache:
            relpath = os.path.relpath(fn_, local_cache_dir)
            relname = os.path.splitext(relpath)[0].replace(os.sep, '.')

            saltpath = os.path.relpath(fn_, local_cache_base_dir)
            filenamed = fileserver.find_file(saltpath, sub_env)

            remote.add(relpath)
            dest = os.path.join(mod_dir, relpath)

            if not os.path.isfile(dest):
                dest_dir = os.path.dirname(dest)
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copyfile(fn_, dest)
                ret.append('{0}.{1}'.format(form, relname))

            # Test to see if already mounted (bound)
            cmd = ['findmnt', dest]
            proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
            proc.wait()

            if proc.returncode:
                cmd = ['mount', '--bind', filenamed['path'], dest]
                proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
                proc.wait()
            elif umount:
                cmd = ['umount', dest]
                proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
                proc.wait()

    touched = bool(ret)
    if __opts__.get('clean_dynamic_modules', True):
        current = set(_listdir_recursively(mod_dir))
        for fn_ in current - remote:
            full = os.path.join(mod_dir, fn_)

            if os.path.ismount(full):
                proc = subprocess.Popen(['umount', full])
                proc.wait()

            if os.path.isfile(full):
                touched = True
                os.remove(full)

        # Cleanup empty dirs
        while True:
            emptydirs = _list_emptydirs(mod_dir)
            if not emptydirs:
                break
            for emptydir in emptydirs:
                touched = True
                shutil.rmtree(emptydir, ignore_errors=True)

    # Dest mod_dir is touched? trigger reload if requested
    if touched:
        mod_file = os.path.join(__opts__['cachedir'], 'module_refresh')
        with salt.utils.fopen(mod_file, 'a+') as ofile:
            ofile.write('')
    return ret


def bind_dirs(umount):
    _bind('beacons', umount=umount)
    _bind('modules', umount=umount)
    _bind('states', umount=umount)
    _bind('grains', umount=umount)
    _bind('renderers', umount=umount)
    _bind('returners', umount=umount)
    _bind('outputters', umount=umount)
    _bind('utils', umount=umount)

if __name__ == '__main__':
    argv = sys.argv

    def join_path(basepath, paths):
        return [os.path.join(basepath, path) for path in paths]

    if BIND or BIND is False:
        umount = not BIND
        path = BASE_DIR.split(os.sep)
        srv_dir = '/srv'
        if srv_dir.lstrip(os.sep) in path:
            index = BASE_DIR.index(srv_dir)
            basepath = os.sep.join(path[:6+1])
            cur_dirs = join_path(basepath, os.listdir(basepath))
            srv_dirs = join_path(srv_dir, os.listdir(srv_dir))

            for path in cur_dirs:
                if path not in srv_dirs:
                    basename = os.path.basename(path)
                    if basename in os.listdir(srv_dir):
                        dest = os.path.join(srv_dir, basename)

                        # Test to see if already mounted (bound)
                        cmd = ['findmnt', dest]
                        proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
                        proc.wait()

                        if proc.returncode:
                            print 'mounting:', path, dest
                            cmd = ['mount', '--bind', path, dest]
                            proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
                            proc.wait()
                        elif umount:
                            cmd = ['umount', dest]
                            proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=subprocess.STDOUT)
                            proc.wait()

        # Bind custom modules
        bind_dirs(umount)

        if not BIND:
            sys.exit()

    salt_call()
