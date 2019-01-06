#!/bin/bash

# Just checking if stuff is installed can take forever on fedora and
# fedora_bootstrap might be called multiple times. We want it fast the second
# time.
if [ ! -e /PFA_INIT ]; then
  echo "Installing required packages"
  # This will install everything needed to run benchmarks on Fedora
  dnf install -y \
    libcgroup-tools \
    time \
    mpich-devel \
    openblas-devel \
    python-numpy

  pip install \
    spambayes \
    humanfriendly

  echo "PFA packages installed" > /PFA_INIT
fi

echo "building benchmarks"
cd /root/benchmarks
build-nat.sh

poweroff
