#!/bin/bash

# This will install everything needed to run benchmarks on Fedora
dnf install -y \
  libcgroup-tools \
  time \
  mpich-devel \
  openblas-devel \
  python-numpy

pip install \
  spambayes

pushd bootstrap

# Set up cgroups, the second command is only needed to avoid a reboot
cp cgconfig.cfg /etc/
cgconfigparser -l /etc/cgconfig.conf

# Set up the PFA systemctl service. By default, this just runs fedora_init.sh,
# but you can modify it to run anything you want so long as that thing also
# calls fedora_init.sh before running pfa stuff.
cp pfa.service /etc/systemd/system/
systemctl enable pfa.service

# Use the commands below to enable the service manually (or offline in e.g. an overlay)
#mkidr -p /etc/systemd/system/default.target.wants/
#ln -s /etc/systemd/system /etc/systemd/system/default.target.wants/pfa.service

popd

./build.sh
