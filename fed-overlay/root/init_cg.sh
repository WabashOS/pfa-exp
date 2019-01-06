#!/bin/bash
echo "+memory" > /sys/fs/cgroup/unified/cgroup.subtree_control
mkdir /sys/fs/cgroup/unified/pfa
