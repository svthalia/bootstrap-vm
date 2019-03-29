#  bootstrap-vm - Bootstrap a VM using libvirt tools
#  Copyright (C) 2019 Jelle Besseling <jelle@pingiun.com>
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
import socket
import subprocess
import sys
import tempfile
import time
from shutil import copyfile

from bootstrap_vm.distributions import Ubuntu
from bootstrap_vm.file_utils import present
from bootstrap_vm.remove import remove
from bootstrap_vm.virtual_machine import VirtualMachine
from bootstrap_vm.config import Config, default_config_file


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


def bootstrap(vm, args):
    if not args['run']:
        vm.distribution.download(vm.image_location)
        vm.distribution.verify(vm.image_location)

    if not args['run']:
        copyfile(vm.image_location, vm.disk_location)
        if args['disk'] != '2G':
            subprocess.run(['qemu-img',
                            'resize',
                            vm.disk_location,
                            args['disk']])

    vm.generate_iso()

    with tempfile.NamedTemporaryFile() as vm_def:
        vm.generate_xml(vm_def.name)
        subprocess.run(['virsh', 'define', vm_def.name], check=True)
        subprocess.run(['virsh', 'create', vm_def.name], check=True)
    subprocess.run(['virsh', 'autostart', vm.name], check=True)

    print("Waiting for IP address")
    ip = False
    if args['ip']:
        ip = args['ip']

    hostname = f'{vm.name}.{config.domain}'
    if args['hostname']:
        hostname = args['hostname']

    while not ip:
        ip = get_ip(vm.name)
        time.sleep(1)

    print(f"The address for {hostname} is {ip}")
    if not args['hostname']:
        print(f"Putting {hostname} in /etc/hosts")
        present('/etc/hosts', hostname + '$', f'{ip} {hostname}')

    if not args['no_install']:
        print("Installing initial packages on the virtual machine")
        returncode = 1
        command = [
            'ssh',
            '-o',
            'StrictHostKeyChecking=no',
            f'ubuntu@{ip}',
            '--',
            "sudo DEBIAN_FRONTEND=noninteractive apt-get -qy update &&"
            " sudo DEBIAN_FRONTEND=noninteractivex "
            f"apt-get install -qy {' '.join(config.initial_packages)}"
        ]
        while returncode != 0:
            out = subprocess.run(command, stdin=sys.stdin, stderr=subprocess.PIPE)
            returncode = out.returncode
            if returncode != 0 and b'Connection refused' not in out.stderr and b'No route to host' not in out.stderr:
                print("Installing packages failed, error:", out.stderr)
                print("Maybe you can run the command manually:")
                print()
                print('sudo ' + ' '.join(f'"{sub}"' if ' ' in sub else sub for sub in command))
                print()
                break
            time.sleep(1)

    print("You can run the following command (on your local machine, only needed once) "
          "to configure ssh with easy access to all VMs:")
    print()
    print(f'echo -e "Host *.{config.domain}\\n\\tProxyCommand ssh {socket.getfqdn()} nc %h %p" >> ~/.ssh/config')
    print()
    print("You have access to the (sudo enabled) user `ubuntu` by default")


def bootstrap_vm():
    parser = argparse.ArgumentParser(description="Bootstrap a VM using virt-install and ansible")
    parser.add_argument('--variant', help="the distribution variant to use")
    parser.add_argument('-r', '--run', action='store_true', help="start an existing disk")
    parser.add_argument('-c', '--config', help="config file to use")
    parser.add_argument('--static', help="use this config key from your static_configs")
    parser.add_argument('--bridge', help="bridge to use for static network")
    parser.add_argument('--ip', help="ip to use for static network")
    parser.add_argument('--hostname', help="hostname to use for static network")
    parser.add_argument('--netplan', help="netplan config to use")
    parser.add_argument('--vcpu', type=int, help="amount of VCPUs")
    parser.add_argument('--memory', type=int, help="amount of memory")
    parser.add_argument('--disk', help="disk size (use format that qemu-img understands)")
    parser.add_argument('--host-keys', help="directory where ssh host-keys can be found for the created VM")
    parser.add_argument('-k', '--key', action='append', dest='public_keys',
                        help="add this public key to the authorized_keys on the created VM")
    parser.add_argument('--no-clean', action='store_true', help="do not clean up files and vms when an error occurs")
    parser.add_argument('--no-install', action='store_true',
                        help="do not install packages (with apt) necessary to run ansible")
    parser.add_argument('name', help="the name for the virtual machine")

    args = vars(parser.parse_args())

    if args['config']:
        global config
        config = Config(args['config'])
    else:
        config = Config(default_config_file())

    name = args['name']
    variant = args['variant']

    try:
        args['distribution'] = Ubuntu(variant)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    static = args['static']
    if static:
        args['bridge'] = args['bridge'] or config.static[static].get('bridge')
        args['ip'] = args['ip'] or config.static[static].get('ip')
        args['hostname'] = args['hostname'] or config.static[static].get('hostname') or None
        args['netplan'] = args['netplan'] or config.static[static].get('netplan') or config.get('netplan') or None
        args['vcpu'] = args['vcpu'] or config.static[static].get('vcpu') or config.vcpu
        args['memory'] = args['memory'] or config.static[static].get('memory') or config.memory
        args['disk'] = args['disk'] or config.static[static].get('disk') or config.disk
        args['host_keys'] = args['host_keys'] or config.static[static].get('host_keys') \
            or config.get('host_keys') or None
        args['public_keys'] = {*(config.static[static].get('public_keys') or []), *(config.get('public_keys') or []),
                               *(args['public_keys'] or [])}
    else:
        args['netplan'] = args['netplan'] or config.get('netplan') or None
        args['vcpu'] = args['vcpu'] or config.vcpu
        args['memory'] = args['memory'] or config.memory
        args['disk'] = args['disk'] or config.disk
        args['host_keys'] = args['host_keys'] or config.get('host_keys') or None
        args['public_keys'] = {*(config.get('public_keys') or []), *(args['public_keys'] or [])}

    del args['config']
    vm = VirtualMachine(config=config, **args)

    if os.path.isfile(vm.disk_location) and not args['run']:
        print(f"The virtual machine {name} already exists", file=sys.stderr)
        sys.exit(1)

    try:
        bootstrap(vm, args)
    except (Exception, KeyboardInterrupt) as e:
        if args['no_clean']:
            print("An error or interrupt occured but no-clean was specified")
            raise e
        remove(name, config, confirm=False)
        if not isinstance(e, KeyboardInterrupt):
            raise e
