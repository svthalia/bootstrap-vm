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

from bootstrap_vm.constants import IMAGES_PATH, ISO_PATH
from bootstrap_vm.file_utils import absent


def remove(name, confirm=True):
    commands = [
        ['virsh', 'destroy', name],
        ['virsh', 'undefine', name],
        ['rm', os.path.join(IMAGES_PATH, f'{name}.img')],
        ['rm', os.path.join(ISO_PATH, f'{name}.iso')],
        ['ssh-keygen', '-f', '/root/.ssh/known_hosts', '-R', f'{name}.fredvm']
    ]
    for command in commands:
        print(' '.join(command))
        if not confirm or input("Do you want to run this? [Y/n] ").lower() != 'n':
            subprocess.run(command)

    print("Removing ip from /etc/hosts")
    if not confirm or input("Do you want to run this? [Y/n] ").lower() != 'n':
        absent('/etc/hosts', name + '.fredvm$')


def remove_vm():
    parser = argparse.ArgumentParser(description="Remove a vm that was created using the boostrap-vm script")
    parser.add_argument('--step', action='store_true', help="one-step-at-a-time: confirm each task before running")
    parser.add_argument('name', nargs='+', help="the name of the virtual machine you want to remove")

    args = vars(parser.parse_args())

    for name in args['name']:
        remove(name, args['step'])
