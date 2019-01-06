#!/bin/bash
# Setup swap
mkswap /dev/ram0
swapon /dev/ram0
echo 0 > /proc/sys/vm/page-cluster

# Setup Cgroups
# echo "+memory" > /sys/fs/cgroup/unified/cgroup.subtree_control
# mkdir /sys/fs/cgroup/unified/pfa
