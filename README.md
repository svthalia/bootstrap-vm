As this software is not used by us anymore, development has stalled.

# bootstrap-vm [![Build Status](https://travis-ci.org/thaliawww/bootstrap-vm.svg?branch=master)](https://travis-ci.org/thaliawww/bootstrap-vm)

Bootstrap a VM using libvirt tools

## Usage
```
usage: bootstrap-vm [-h] [--variant VARIANT] [-r] [-c CONFIG]
                    [--static STATIC] [--bridge BRIDGE] [--ip IP]
                    [--hostname HOSTNAME] [--netplan NETPLAN] [--vcpu VCPU]
                    [--memory MEMORY] [--disk DISK] [--host-keys HOST_KEYS]
                    [-k PUBLIC_KEYS] [--no-clean] [--no-install]
                    name

Bootstrap a VM using virt-install and ansible

positional arguments:
  name                  the name for the virtual machine

optional arguments:
  -h, --help            show this help message and exit
  --variant VARIANT     the distribution variant to use
  -r, --run             start an existing disk
  -c CONFIG, --config CONFIG
                        config file to use
  --static STATIC       use this config key from your static_configs
  --bridge BRIDGE       bridge to use for static network
  --ip IP               ip to use for static network
  --hostname HOSTNAME   hostname to use for static network
  --netplan NETPLAN     netplan config to use
  --vcpu VCPU           amount of VCPUs
  --memory MEMORY       amount of memory
  --disk DISK           disk size (use format that qemu-img understands)
  --host-keys HOST_KEYS
                        directory where ssh host-keys can be found for the
                        created VM
  -k PUBLIC_KEYS, --key PUBLIC_KEYS
                        add this public key to the authorized_keys on the
                        created VM
  --no-clean            do not clean up files and vms when an error occurs
  --no-install          do not install packages (with apt) necessary to run
                        ansible
```

If the `-c/--config` option is not supplied, the default config locations are tried: if the `XDG_CONFIG_DIRS` variable exists, the first directory is used, otherwise `/etc/bootstrap-vm/config.yaml` will be read.

This configuration file allows you to set the default values for the `netplan`, `vcpu`, `memory`, `disk`, `host_keys`, and `public_keys` options.

Additionally there is the concept of "static" configurations, which are a named grouped configuration for a specific VM which is created multiple times.

## Warning

This script is written to be used on our own servers. This means that a lot of 
things are hardcoded, and there are no guarantees that the script will run on
any other server configurations.

For reference, we are using this configuration:

- Ubuntu 18.04 with KVM virtualization
- A guest, virtualivo, which would be running on a bridge, but this is configurable
- Other guests which are NATed by libvirt
- All guests are running Ubuntu
- We manage configuration with ansible

## Installing

bootstrap-vm needs some external packages, on ubuntu you can install these with
`apt`:

- genisoimage
- libvirt-bin

You also need to get the Ubuntu cloudimage signing key, otherwise the hash 
verification of the image will fail.

Now you can install the script using pip:

```bash
sudo -H pip install git+https://github.com/thaliawww/bootstrap-vm
```
