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

cd /root
./build.sh

poweroff
