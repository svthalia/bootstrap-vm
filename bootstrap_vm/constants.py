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

LIBVIRT_PATH = '/var/lib/libvirt/'
IMAGES_PATH = os.path.join(LIBVIRT_PATH, 'images')
ISO_PATH = os.path.join(LIBVIRT_PATH, 'iso')
ONE_DAY = 60 * 60 * 24

VM_XML = """
<domain type="kvm">
  <name>{name}</name>
  <uuid>{uuid}</uuid>
  <metadata>
    <libosinfo:libosinfo xmlns:libosinfo="http://libosinfo.org/xmlns/libvirt/domain/1.0">
      <libosinfo:os id="{osid}"/>
    </libosinfo:libosinfo>
  </metadata>
  <memory>{memory}</memory>
  <currentMemory>{memory}</currentMemory>
  <vcpu>{vcpu}</vcpu>
  <os>
    <type arch="x86_64" machine="pc-i440fx-bionic">hvm</type>
    <boot dev="hd"/>
  </os>
  <features>
    <acpi/>
    <apic/>
  </features>
  <cpu mode="host-model"/>
  <clock offset="utc">
    <timer name="rtc" tickpolicy="catchup"/>
    <timer name="pit" tickpolicy="delay"/>
    <timer name="hpet" present="no"/>
  </clock>
  <pm>
    <suspend-to-mem enabled="no"/>
    <suspend-to-disk enabled="no"/>
  </pm>
  <devices>
    <emulator>/usr/bin/kvm-spice</emulator>
    <disk type="file" device="disk">
      <driver name="qemu" type="qcow2"/>
      <source file="{disk_location}"/>
      <target dev="vda" bus="virtio"/>
    </disk>
    <disk type="file" device="cdrom">
      <driver name="qemu" type="raw"/>
      <source file="{iso_location}"/>
      <target dev="hda" bus="ide"/>
      <readonly/>
    </disk>
    <controller type="usb" index="0" model="ich9-ehci1"/>
    <controller type="usb" index="0" model="ich9-uhci1">
      <master startport="0"/>
    </controller>
    <controller type="usb" index="0" model="ich9-uhci2">
      <master startport="2"/>
    </controller>
    <controller type="usb" index="0" model="ich9-uhci3">
      <master startport="4"/>
    </controller>
    {interface}
    <console type="pty">
      <target type="serial"/>
    </console>
    <channel type="unix">
      <source mode="bind"/>
      <target type="virtio" name="org.qemu.guest_agent.0"/>
    </channel>
    <rng model="virtio">
      <backend model="random">/dev/urandom</backend>
    </rng>
  </devices>
</domain>"""

DHCP_INTERFACE = """
<interface type="network">
  <mac address="{macaddress}"/>
  <source network="default"/>
  <model type="virtio"/>
</interface>"""

STATIC_INTERFACE = """
<interface type="bridge">
    <mac address="{macaddress}"/>
    <source bridge="{bridge}"/>
    <model type="virtio"/>
</interface>"""

NETPLAN_VIRTUALIVO = """
version: 2
ethernets:
  ens2:
    match:
      macaddress: "{macaddress}"
    dhcp4: no
    dhcp6: no
    accept-ra: no
    gateway4: 131.174.41.1
    gateway6: 2001:610:1418:1106::1
    addresses:
      - 131.174.41.19/25
      - 2001:610:1418:1106:131:174:41:19/64
    nameservers:
      addresses:
        - "131.174.30.40" # resolver.science.ru.nl
        - "131.174.16.131" # resolvbck.science.ru.nl
      search:
        - "science.ru.nl"
"""
