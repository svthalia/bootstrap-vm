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
import tempfile
import time

from bootstrap_vm.constants import ONE_DAY


class Ubuntu:
    @property
    def distribution(self):
        return 'Ubuntu'

    @property
    def variant(self):
        return self._variant

    urls = {
        'bionic': {
            'image': 'https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-amd64.img',
            'hashes': 'https://cloud-images.ubuntu.com/bionic/current/SHA256SUMS',
            'signature': 'https://cloud-images.ubuntu.com/bionic/current/SHA256SUMS.gpg',
            'libosinfo_id': 'http://ubuntu.com/ubuntu/18.04',
        },
        'xenial': {
            'image': 'https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img',
            'hashes': 'https://cloud-images.ubuntu.com/xenial/current/SHA256SUMS',
            'signature': 'https://cloud-images.ubuntu.com/xenial/current/SHA256SUMS.gpg',
            'libosinfo_id': 'http://ubuntu.com/ubuntu/16.04',
        }
    }

    def __init__(self, variant=None):
        if variant is None:
            variant = 'bionic'
        if variant not in self.urls:
            raise RuntimeError(f"Unknown variant {variant} for Ubuntu")
        self._variant = variant

    def download(self, image_location):
        if os.path.isfile(image_location) and os.path.getctime(image_location) > (time.time() - ONE_DAY):
            return
        raw_location, _ = os.path.splitext(image_location)
        raw_location = raw_location + '.raw'

        if self._variant == 'bionic':
            subprocess.run(['wget', '--inet4-only', '-O', raw_location, self.urls[self._variant]['image']])
            subprocess.run(['qemu-img', 'convert', '-O', 'qcow2', raw_location, image_location])
        elif self._variant == 'xenial':
            subprocess.run(['wget', '--inet4-only', '-O', image_location, self.urls[self._variant]['image']])
        else:
            raise NotImplementedError(f"variant {self._variant} is not supported")

    def verify(self, image_location):
        with tempfile.NamedTemporaryFile() as hashes, \
                tempfile.NamedTemporaryFile() as signature, \
                tempfile.NamedTemporaryFile() as image_hash:
            subprocess.run(['wget', '--inet4-only', '-O', hashes.name, self.urls[self._variant]['hashes']])
            subprocess.run(['wget', '--inet4-only', '-O', signature.name, self.urls[self._variant]['signature']])

            subprocess.run(['gpg', '--homedir', '/root/.gnupg', '--verify', signature.name, hashes.name], check=True)
            filename = self.urls[self._variant]['image'].split('/')[-1]
            folder, image = image_location.rsplit('/', 1)
            image, _ = os.path.splitext(image)

            for line in hashes:
                if line.strip().endswith(bytes(filename, encoding='utf-8')):
                    if self._variant == 'bionic':
                        image_hash.file.write(line.split()[0] + b' ' + bytes(image, encoding='utf-8') + b'.raw\n')
                    else:
                        image_hash.file.write(line.split()[0] + b' ' + bytes(image, encoding='utf-8') + b'.img\n')
                    break
            image_hash.file.close()
            subprocess.run(['sha256sum', '--check', image_hash.name], cwd=folder, check=True)
