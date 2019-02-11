#  bootstrap-vm - Bootstrap a VM using libvirt tools
#  Copyright (C) 2019 Jelle Besseling
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import os
import subprocess
import sys
import tempfile
import time
from shutil import copyfile

from bootstrap_vm.distributions import DISTRIBUTIONS
from bootstrap_vm.file_utils import present
from bootstrap_vm.remove import remove
from bootstrap_vm.virtual_machine import VirtualMachine


def get_ip(name):
    b_name = bytes(name, encoding='utf-8')
    out = subprocess.run(['virsh', 'net-dhcp-leases', 'default'], stdout=subprocess.PIPE)
    for line in sorted(out.stdout.split(b'\n')[2:], reverse=True):
        words = line.split()
        try:
            if words[5] == b_name:
                return str(words[4], encoding='utf-8').split('/')[0]
        except IndexError:
            pass
    return False


def bootstrap(vm, just_run, no_install):
    if not just_run:
        vm.distribution.download(vm.image_location)
        vm.distribution.verify(vm.image_location)

    if not just_run:
        copyfile(vm.image_location, vm.disk_location)

    vm.generate_iso()

    with tempfile.NamedTemporaryFile() as vm_def:
        vm.generate_xml(vm_def.name)
        subprocess.run(['virsh', 'define', vm_def.name], check=True)
        subprocess.run(['virsh', 'create', vm_def.name], check=True)
    subprocess.run(['virsh', 'autostart', vm.name], check=True)

    print("Waiting for IP address")
    ip = False
    if vm.virtualivo:
        ip = "131.174.41.19"
        hostname = 'virtualivo.thalia.nu'
    else:
        hostname = f'{vm.name}.fredvm'

    while not ip:
        ip = get_ip(vm.name)
        time.sleep(1)

    print(f"The address for {hostname} is {ip}")
    if not vm.virtualivo:
        print(f"Putting {hostname} in /etc/hosts")
        present('/etc/hosts', hostname + '$', f'{ip} {hostname}')

    if not no_install:
        print("Installing ansible requirements on the virtual machine")
        returncode = 1
        command = [
            'ssh',
            '-o',
            'StrictHostKeyChecking=no',
            f'ubuntu@{ip}',
            '--',
            "(test -e /usr/bin/python && echo 'python is installed') || (sudo DEBIAN_FRONTEND=noninteractive apt-get -qy update && sudo DEBIAN_FRONTEND=noninteractivex apt-get install -qy qemu-guest-agent python python-apt python-simplejson)"
        ]
        while returncode != 0:
            out = subprocess.run(command, stdin=sys.stdin, stderr=subprocess.PIPE)
            returncode = out.returncode
            if returncode != 0 and b'Connection refused' not in out.stderr and b'No route to host' not in out.stderr:
                print("Installing requirements failed, error:", out.stderr)
                print("Maybe you can run the command manually:")
                print()
                print('sudo ' + ' '.join(f'"{sub}"' if ' ' in sub else sub for sub in command))
                print()
                break
            time.sleep(1)

    print("You can run the following command (on your local machine, only needed once) to configure ssh with easy access to all VMs:")
    print()
    print(f'echo -e "Host *.fredvm\\n\\tProxyCommand ssh fred.thalia.nu nc %h %p" >> ~/.ssh/config')
    print()
    print("You have access to the (sudo enabled) user `ubuntu` by default")
    # TODO: generate copypastable ansible command when we have testing playbooks/environments
    # print("If you have configured ssh, you can run some ansible roles using this command (you can press enter when prompted for a password):")
    # print()
    # print(f'ansible-playbook -u ubuntu -i "{name}," --extra-vars="@environments/defaults.yml" -t common,ssh,users production.yml')


def bootstrap_vm():
    parser = argparse.ArgumentParser(description="Bootstrap a VM using virt-install and ansible")
    parser.add_argument('-d', '--distribution', default='ubuntu', help="the linux distribution to use")
    parser.add_argument('--variant', help="the distribution variant to use")
    parser.add_argument('-r', '--run', action='store_true', help="start an existing disk")
    parser.add_argument('-b', '--bridge', help="use this bridge for networking")
    parser.add_argument('--virtualivo', action='store_true', help="this VM should be setup as virtualivo")
    parser.add_argument('-k', '--key', action='append', help="add this public key to the authorized_keys on the created VM")
    parser.add_argument('--host-keys', help="directory where ssh host-keys can be found for the created VM")
    parser.add_argument('--no-clean', action='store_true', help="do not clean up files and vms when an error occurs")
    parser.add_argument('--no-install', action='store_true', help="do not install packages (with apt) necessary to run ansible")
    parser.add_argument('name', help="the name for the virtual machine")

    args = vars(parser.parse_args())

    name = args['name']
    distribution = args['distribution']
    variant = args['variant']

    if args['virtualivo'] and not args['bridge']:
        args['bridge'] = 'virtualivo-eno2'

    if distribution not in DISTRIBUTIONS:
        print(f"Unknown distribution {distribution}", file=sys.stderr)
        sys.exit(1)

    try:
        args['distribution'] = DISTRIBUTIONS[distribution](variant)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    vm = VirtualMachine(**args)

    if os.path.isfile(vm.disk_location) and not args['run']:
        print(f"The virtual machine {name} already exists", file=sys.stderr)
        sys.exit(1)

    try:
        bootstrap(vm, args['run'], args['no_install'])
    except (Exception, KeyboardInterrupt) as e:
        if args['no_clean']:
            print("An error or interrupt occured but no-clean was specified")
            raise e
        remove(name, confirm=False)
        if not isinstance(e, KeyboardInterrupt):
            raise e
