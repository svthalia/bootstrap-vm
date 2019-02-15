# bootstrap-vm

Bootstrap a VM using libvirt tools

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
sudo pip install https://github.com/thaliawww/bootstrap-vm
```
