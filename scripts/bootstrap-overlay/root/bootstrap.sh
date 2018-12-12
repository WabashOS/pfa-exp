#!/bin/bash
set -e

dnf install -y git
git clone git@github.com:WabashOS/pfa-exp.git
pushd pfa-exp
git submodule update --init --recursive
cd scripts
./fedora_bootstrap.sh

popd
