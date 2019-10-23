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
import subprocess
import uuid

from bootstrap_vm.config import Config
from bootstrap_vm.constants import STATIC_INTERFACE, DHCP_INTERFACE, VM_XML


class VirtualMachine:
    def __init__(self, name: str, distribution, config: Config, **kwargs: dict):
        self.name = name
        self.distribution = distribution
        self.macaddress = "52:54:00:" + ":".join(
            "{:02x}".format(byte) for byte in os.urandom(3)
        )
        self.config = config
        self.args = kwargs

    @property
    def image_location(self):
        return os.path.join(
            self.config.images_path,
            f"{self.distribution.distribution}-{self.distribution.variant}.img",
        )

    @property
    def disk_location(self):
        return os.path.join(self.config.images_path, f"{self.name}.img")

    @property
    def iso_location(self):
        return os.path.join(self.config.iso_path, f"{self.name}.iso")

    @staticmethod
    def write_ssh_key(f, host_keys, keytype):
        sec_key_path = os.path.join(host_keys, f"ssh_host_{keytype}_key")
        if os.path.isfile(sec_key_path):
            f.write(f"  {keytype}_private: |\n")
            with open(sec_key_path) as key:
                for line in key:
                    f.write("    " + line)
            f.write("\n")
        pub_key_path = sec_key_path + ".pub"
        if os.path.isfile(pub_key_path):
            f.write(f"  {keytype}_public: |\n")
            with open(pub_key_path) as key:
                for line in key:
                    f.write("    " + line)
            f.write("\n")

    def generate_iso(self):
        # cloud-init from the ubuntu cloud image uses a cdrom with metadata information
        # we use this to set up the authorized keys using the authorized keys from the home
        # directory, and the public key from the root user
        os.makedirs(self.config.iso_path, mode=0o0711, exist_ok=True)
        iso_files = list()
        metadata_location = os.path.join(self.config.iso_path, "meta-data")
        iso_files.append(metadata_location)
        with open(metadata_location, "w") as f:
            f.write(f"local-hostname: {self.name}\n")
            f.write(f"public-keys:\n")
            authorized_keys = os.path.join(
                os.path.expanduser("~"), ".ssh", "authorized_keys"
            )
            if os.path.isfile(authorized_keys):
                with open(authorized_keys) as keys:
                    for line in keys:
                        f.write("  - " + line)
            root_key = "/root/.ssh/id_ed25519.pub"
            if os.path.isfile(root_key):
                with open(root_key) as key:
                    f.write("  - " + key.read().strip() + "\n")
            if self.args["public_keys"]:
                for key in self.args["public_keys"]:
                    for line in key.split("\n"):
                        if line.strip() != "":
                            f.write("  - " + line.strip() + "\n")

        # This file only needs to be touched
        userdata_location = os.path.join(self.config.iso_path, "user-data")
        iso_files.append(userdata_location)
        with open(userdata_location, "w") as f:
            if self.args["host_keys"]:
                print(f"Placing host-keys from {self.args['host_keys']}")
                f.write("#cloud-config\n\n")
                f.write("ssh_keys:\n")
                for keytype in ["ed25519", "rsa", "ecdsa"]:
                    self.write_ssh_key(f, self.args["host_keys"], keytype)

        if self.args["netplan"]:
            network_config_location = os.path.join(
                self.config.iso_path, "network-config"
            )
            iso_files.append(network_config_location)
            with open(network_config_location, "w") as f, open(
                self.args["netplan"]
            ) as netplan:
                f.write(netplan.read().format(macaddress=self.macaddress))

        subprocess.run(
            [
                "genisoimage",
                "-o",
                self.iso_location,
                "-V",
                "cidata",
                "-r",
                "-J",
                *iso_files,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def generate_xml(self, filename: str):
        vm_uuid = str(uuid.uuid4())
        if self.args["bridge"]:
            interface = STATIC_INTERFACE.format(
                bridge=self.args["bridge"], macaddress=self.macaddress
            )
        else:
            interface = DHCP_INTERFACE.format(macaddress=self.macaddress)
        vm_def = VM_XML.format(
            name=self.name,
            uuid=vm_uuid,
            memory=self.args["memory"],
            vcpu=self.args["vcpu"],
            disk_location=self.disk_location,
            iso_location=self.iso_location,
            osid=self.distribution.urls[self.distribution.variant]["libosinfo_id"],
            interface=interface,
        )
        print(vm_def)
        with open(filename, "w") as f:
            f.write(vm_def)
