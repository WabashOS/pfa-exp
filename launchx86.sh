#!/bin/bash
qemu-system-x86_64 -name fedora-cloud \
 -s \
 -m 8192 \
 -cpu host \
 -enable-kvm \
 -hda fed.qcow2 \
 -device e1000,netdev=net0 \
 -netdev user,id=net0,hostfwd=tcp::5555-:22 \
 -nographic

# qemu-system-x86_64 -name centos \
#  -m 2048 \
#  -drive format=raw,file=centos.img \
#  -device e1000,netdev=net0 \
#  -netdev user,id=net0,hostfwd=tcp::5555-:22 \
#  -nographic
