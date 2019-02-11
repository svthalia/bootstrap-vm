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

import os
import sys

from bootstrap_vm.bootstrap import bootstrap_vm
from bootstrap_vm.remove import remove_vm


def main():
    if os.geteuid() != 0:
        print("You need to be root to run this script", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(sys.argv[0])
    if filename == 'bootstrap-vm':
        bootstrap_vm()
    elif filename == 'remove-vm':
        remove_vm()
    else:
        print("Filename should be bootstrap-vm or remove-vm", file=sys.stderr)


if __name__ == '__main__':
    main()
