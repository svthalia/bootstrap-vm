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

import os

import yaml

from bootstrap_vm.constants import APP_NAME

DEFAULT_CONFIG = {
    'initial_packages': ['qemu-guest-agent', 'python', 'python-apt', 'python-simplejson'],
    'vcpu': 1,
    'memory': 1048576,
    'domain': 'test',
    'base_path': '/var/lib/libvirt/',
    'iso_path': '/var/lib/libvirt/iso',
    'images_path': '/var/lib/libvirt/images',
}


class Config:
    def __init__(self, filename):
        if os.path.isfile(filename):
            file = open(filename)
            self._content = {**DEFAULT_CONFIG, **yaml.safe_load(file.read())}
        else:
            self._content = DEFAULT_CONFIG

    def __getattr__(self, item):
        return self._content[item]


# Adapted from poetry:
# https://github.com/sdispater/poetry/blob/2f2cec03b6b14e882522f7f6042ecdafebda2ca5/poetry/utils/appdirs.py
def expanduser(path):
    """
    Expand ~ and ~user constructions.
    Includes a workaround for http://bugs.python.org/issue14768
    """
    expanded = os.path.expanduser(path)
    if path.startswith("~/") and expanded.startswith("//"):
        expanded = expanded[1:]
    return expanded


# Adapted from poetry:
# https://github.com/sdispater/poetry/blob/2f2cec03b6b14e882522f7f6042ecdafebda2ca5/poetry/utils/appdirs.py
def get_site_config(appname):
    xdg_config_dirs = os.getenv("XDG_CONFIG_DIRS", [])
    if xdg_config_dirs:
        pathlist = [
            os.path.join(expanduser(x), appname)
            for x in xdg_config_dirs.split(os.pathsep)
        ]
    else:
        pathlist = []

    # always look in /etc directly as well
    pathlist.append("/etc")
    return os.path.join(pathlist[0], appname)


def default_config_file():
    return os.path.join(get_site_config(APP_NAME), 'config.yaml')
