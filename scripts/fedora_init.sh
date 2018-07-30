#!/bin/bash
#Setup swap
mkswap /dev/ram0
swapon /dev/ram0
echo 0 > /proc/sys/vm/page-cluster
