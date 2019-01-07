#!/bin/sh

# Handy to have this saved for reference later
cp /proc/config.gz .

cd /root/util/
./init_swap.sh
./init_cgrp.sh

# Install commands (to avoid annoying paths)
ln -s /root/util/pfa_launch /bin/
ln -s /root/util/reset_cg /bin/
ln -s /root/util/run_cg /bin/
ln -s /root/util/mytime /bin/
