#!/bin/bash
# Setup swap
mkswap /dev/ram0
swapon /dev/ram0
echo 0 > /proc/sys/vm/page-cluster


if [ ! -f /bin/pfa_launch ]; then
  ln -s /root/util/pfa_launch /bin/
  ln -s /root/util/pfa_exec /bin/
  ln -s /root/util/run_cg /bin/
  ln -s /root/util/reset_cg /bin/
fi
