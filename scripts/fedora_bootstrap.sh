#!/bin/bash

# This will install everything needed to run benchmarks on Fedora
dnf install -y \
  libcgroup-tools \
  time \
  mpich-devel \
  openblas-devel

pushd bootstrap

cp cgconfig.cfg /etc/
cp pfa.service /etc/systemd/system/
ln -s /etc/systemd/system /etc/systemd/system/default.target.wants/pfa.service

popd

./build.sh
