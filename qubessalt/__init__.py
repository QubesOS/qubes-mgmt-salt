# coding=utf-8
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2016  Marek Marczykowski-Górecki
#                                   <marmarek@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
#
import logging
import multiprocessing
import os
import shlex
import tempfile
import shutil
import subprocess
import sys
import time

import grp

import fcntl
import yaml
import salt.client
import salt.config
import qubesadmin.exc
import qubesadmin.vm
try:
    import qubessaltpatches
except ImportError:
    pass

FORMAT_LOG = '%(asctime)s %(message)s'
LOGPATH = '/var/log/qubes'

formatter_log = logging.Formatter(FORMAT_LOG)

class ManageVM(object):
    def __init__(self, app, vm, mgmt_template=None, force_color=False):
        super(ManageVM, self).__init__()
        self.vm = vm
        self.app = app
        self.log = logging.getLogger('qubessalt.vm.' + vm.name)
        self.log_path = os.path.join(LOGPATH, 'mgmt-{}.log'.format(vm.name))
        handler_log = logging.FileHandler(
            self.log_path,
            encoding='utf-8')
        handler_log.setFormatter(formatter_log)
        self.log.addHandler(handler_log)
        self.force_color = force_color

        self.log.propagate = False
        if mgmt_template is not None:
            self.mgmt_template = mgmt_template
        else:
            try:
                self.mgmt_template = vm.management_dispvm
            except AttributeError:
                # old core
                self.mgmt_template = self.app.default_dispvm

        if self.mgmt_template is None:
            raise qubesadmin.exc.QubesException(
                'DVM template for management not selected. '
                'Execute \'sudo qubesctl state.sls qvm.default-mgmt-dvm\' or '
                'create it manually and set management_dispvm property.')

    def prepare_salt_config_for_vm(self):
        tmpdir = tempfile.mkdtemp()
        output_dir = os.path.join(tmpdir, 'srv')
        shutil.copytree('/srv', output_dir)
        # make sure only pillars for given host are sent

        p = subprocess.Popen(
            ['qubesctl', '--dom0-only',
                '--id={}'.format(self.vm.name), '--output=yaml',
                'pillar.items'], stdout=subprocess.PIPE)
        (pillar_items_output, _) = p.communicate()
        pillar_data = yaml.safe_load(pillar_items_output.decode())
        pillar_data = pillar_data['local']
        # remove source pillar files
        # TODO: remove also pillar modules
        for roots in pillar_data['master']['pillar_roots'].values():
            for root in roots:
                # do not use os.path.join on purpose - root is absolute path
                pillar_path = tmpdir + root
                if os.path.exists(pillar_path):
                    shutil.rmtree(tmpdir + root)

        extmod_cache = pillar_data['master'].get('extension_modules',
                                    '/var/cache/salt/minion/extmods')
        if os.path.exists(extmod_cache):
            shutil.copytree(extmod_cache, os.path.join(output_dir, "_extmods"))

        # pass selected configuration options
        master_conf = {}
        for opt in ['file_roots']:
            if opt in pillar_data['master']:
                master_conf[opt] = pillar_data['master'][opt]
        with open(os.path.join(output_dir, 'master'), 'w') as f:
            f.write(yaml.safe_dump(master_conf))

        # remove unneeded pillar entries
        for entry in ('master',):
            if entry in pillar_data:
                del pillar_data[entry]

        # save rendered pillar data
        pillar_dir = os.path.join(output_dir, 'pillar')
        os.mkdir(pillar_dir)
        with open(os.path.join(pillar_dir, 'combined.sls'), 'w') as f:
            f.write(yaml.safe_dump(pillar_data))
        # TODO only selected environments?
        with open(os.path.join(pillar_dir, 'top.sls'), 'w') as f:
            f.write(yaml.safe_dump(
                {'base':
                    {self.vm.name: ['combined']}}))
        return output_dir

    def salt_call(self, command='state.highstate', return_output=False):
        exit_code = 0
        self.log.info('calling \'%s\'...', command)
        appvmtpl = self.mgmt_template

        name = 'disp-mgmt-{}'.format(self.vm.name)
        # name is limited to 31 chars
        if len(name) > 31:
            name = name[:31]
        try:
            dispvm = self.app.domains[name]
        except KeyError:
            dispvm = self.app.add_new_vm('DispVM',
                template=appvmtpl,
                label=appvmtpl.label,
                name=name)
            dispvm.features['internal'] = True
            dispvm.features['gui'] = False
            dispvm.netvm = None
            dispvm.auto_cleanup = True
        qrexec_policy(dispvm.name, self.vm.name, True)
        return_data = "NO RESULT"
        try:
            initially_running = self.vm.is_running()
            if not dispvm.is_running():
                dispvm.start()
            # Workaround for https://github.com/saltstack/salt/issues/60003
            salt_fixup = b"""
if [ -e /etc/fedora-release ]; then
    sed -i -e 's/if cached_client is None:/if cached_client is None or cached_client.opts["cachedir"] != self.opts["cachedir"]:/' \\
        -e 's/not hasattr(cached_client, "opts")/\\0 or cached_client.opts["cachedir"] != self.opts["cachedir"]/' \\
            /usr/lib/python3*/site-packages/salt/utils/jinja.py
    sed -i -e 's/self.functions = salt.loader.ssh_wrapper.*/self.functions = self.wrapper/' \\
            /usr/lib/python3*/site-packages/salt/client/ssh/state.py
fi
"""
            fixup_proc = dispvm.run_service('qubes.VMRootShell', user='root')
            (untrusted_stdout, untrusted_stderr) = fixup_proc.communicate(salt_fixup)
            if fixup_proc.returncode != 0:
                stderr = '|'.join(''.join(
                    [c for c in line if 0x20 <= ord(c) <= 0x7e])
                    for line in untrusted_stderr
                                  .decode('ascii', errors='ignore')
                                  .splitlines())
                self.log.warning('Failed to apply salt#60003 workaround: %s',
                                 stderr)
            # Copy whole Salt configuration
            salt_config = self.prepare_salt_config_for_vm()
            retcode = dispvm.run_service(
                'qubes.Filecopy',
                localcmd='/usr/lib/qubes/qfile-dom0-agent {}'.format(
                    shlex.quote(salt_config))).wait()
            shutil.rmtree(salt_config)
            if retcode != 0:
                raise qubesadmin.exc.QubesException(
                    "Failed to copy Salt configuration to {}".
                    format(dispvm.name))
            p = dispvm.run_service('qubes.SaltLinuxVM', user='root')
            (untrusted_stdout, untrusted_stderr) = p.communicate(
                    (self.vm.name + '\n' + command + '\n').encode())
            untrusted_stdout = untrusted_stdout.decode('ascii', errors='ignore') + \
                               untrusted_stderr.decode('ascii', errors='ignore')
            if not self.force_color:
                # removing control characters, unless colors are enabled
                stdout_lines = [
                    ''.join([c for c in line if ord(c) >= 0x20 and ord(c) <= 0x7e])
                    for line in untrusted_stdout.splitlines()]
            else:
                stdout_lines = untrusted_stdout.splitlines()

            for line in stdout_lines:
                self.log.info('output: %s', line)
            if stdout_lines[0].count(self.vm.name + ':') == 1:
                stdout_lines = stdout_lines[1:]
            self.log.info('exit code: %d', p.returncode)
            exit_code = p.returncode
            if exit_code == 0 and command.startswith('state.') and not stdout_lines:
                # heuristic to detect silent failures - salt-ssh may exit with
                # 0 in those cases
                exit_code = 1
                return_data = "ERROR (exit code 0, but no changes summary)"
                self.log.info('missing changes summary, considering it a failure')
            elif return_output and stdout_lines:
                return_data = stdout_lines
            elif p.returncode == 127:
                return_data = "ERROR (missing qubes-mgmt-salt-vm-connector " \
                    "package in {!s} (template of {!s}))".format(
                        getattr(self.mgmt_template, 'template',
                            self.mgmt_template),
                        self.mgmt_template)
            else:
                if p.returncode == 0:
                    return_data = "OK"
                elif p.returncode == 20:
                    return_data = "NOTHING TO DO"
                else:
                    return_data = "ERROR (exit code {}, details in {})".format(
                        p.returncode, self.log_path)
            if self.vm.is_running() and not initially_running:
                self.vm.shutdown()
                # FIXME: convert to self.vm.shutdown(wait=True) in core3
                while self.vm.is_running():
                    time.sleep(1)
        finally:
            qrexec_policy(dispvm.name, self.vm.name, False)
            try:
                dispvm.kill()
            except (qubesadmin.exc.QubesVMNotStartedError,
                    qubesadmin.exc.QubesDaemonNoResponseError):
                pass
        return exit_code, return_data


def load_opts():
    opts = salt.config.minion_config('/etc/salt/minion')
    opts['file_client'] = 'local'
    return opts


def has_config(vm):
    opts = load_opts()
    opts['id'] = vm
    caller = salt.client.Caller(mopts=opts)
    top = caller.cmd('state.show_top', queue=False, concurrent=True)
    return bool(top)


def run_one(vmname, command, show_output, force_color, skip_top_check):
    uses_top = False
    if 'state.highstate' in command:
        uses_top = True
    # there could be some options after, but lean on the safe side - better
    # just disable optimization than skip some state to apply
    if command[-1] == 'state.apply':
        uses_top = True
    if not skip_top_check and uses_top:
        try:
            if not has_config(vmname):
                return vmname, 0, "SKIP (nothing to do)"
        except Exception as err:  # pylint: disable=broad-except
            return vmname, 1, f"ERROR (exception {err})"
    app = qubesadmin.Qubes()
    try:
        vm = app.domains[vmname]
    except KeyError:
        return vmname, 2, "ERROR (vm not found)"
    try:
        runner = ManageVM(app, vm, force_color=force_color)
        exit_code, result = runner.salt_call(
            ' '.join([shlex.quote(word) for word in command]),
            return_output=show_output)
    except Exception as e:  # pylint: disable=broad-except
        return vmname, 1, "ERROR (exception {})".format(str(e))
    return vm.name, exit_code, result


class ManageVMRunner(object):
    """Call salt in multiple VMs at the same time"""

    def __init__(self, app, vms, command, max_concurrency=4, show_output=False,
            force_color=False, skip_top_check=False):
        super(ManageVMRunner, self).__init__()
        self.vms = vms
        self.app = app
        self.command = command
        self.max_concurrency = max_concurrency
        self.show_output = show_output
        self.force_color = force_color
        self.skip_top_check = skip_top_check
        self.exit_code = 0

        # this do patch already imported salt modules
        try:
            import qubessaltpatches
        except ImportError:
            pass

    def collect_result(self, result_tuple):
        name, exit_code, result = result_tuple
        self.exit_code = max(self.exit_code, exit_code)
        if self.show_output and isinstance(result, list):
            sys.stdout.write(name + ":\n")
            sys.stdout.write('\n'.join(['  ' + line for line in result]))
            sys.stdout.write('\n')
        else:
            print(name + ": " + result)

    def run(self):
        pool = multiprocessing.Pool(self.max_concurrency)
        for vm in self.vms:
            pool.apply_async(run_one,
                (vm.name, self.command, self.show_output, self.force_color,
                    self.skip_top_check),
                callback=self.collect_result
            )
        pool.close()
        pool.join()
        return self.exit_code


def qrexec_policy(src, dst, allow):
    while True:
        path = '/etc/qubes/policy.d/30-qubesctl-salt.policy'
        # Mode is a bit tricky here. We want to *atomically*:
        # - open an existing file for reading (do not truncate it)
        # - if the file does not exist - create it
        # The above means neither 'r+' (fails on non-existing file)
        # nor 'w+' (truncates existing file) works.
        # 'a+' fits here, although is a bit weird.
        with open(path, 'a+') as policy:
            # take the lock here, it's released by closing the file
            fcntl.lockf(policy.fileno(), fcntl.LOCK_EX)
            # While we were waiting for lock, someone could have unlink()ed
            # (or rename()d) our file out of the filesystem. We have to
            # ensure we got lock on something linked to filesystem.
            # If not, try again.

            try:
                if os.fstat(policy.fileno()) != os.stat(path):
                    continue
            except FileNotFoundError:
                continue

            policy.seek(0)
            policy_rules = policy.readlines()
            if not policy_rules:
                policy_rules = [
                    '# DO NOT EDIT: automatically generated file\n',
                    '# This file is managed by qubesctl tool\n',
                ]
            services = ('qubes.Filecopy', 'qubes.VMShell', 'qubes.VMRootShell')
            for service in services:
                line = "{} * {} {} allow user=root\n".format(service, src, dst)
                if allow:
                    policy_rules.append(line)
                else:
                    try:
                        policy_rules.remove(line)
                    except ValueError:
                        # already removed
                        pass

            # if only comments left, remove the file
            if not [l for l in policy_rules if not l.startswith('#')]:
                os.unlink(path)
            else:
                with tempfile.NamedTemporaryFile(
                        prefix=path, delete=False, mode='w+') as policy_new:
                    policy_new.write(''.join(policy_rules))
                    policy_new.flush()
                    try:
                        os.chown(policy_new.name, -1,
                            grp.getgrnam('qubes').gr_gid)
                        os.chmod(policy_new.name, 0o660)
                    except KeyError:  # group 'qubes' not found
                        # don't change mode if no 'qubes' group in the system
                        pass
                os.rename(policy_new.name, path)
        break
