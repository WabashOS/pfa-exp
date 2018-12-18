Collection of automated and repeatable experiments for the PFA.

# Installation
This repo is designed to work with firesim-software
(https://github.com/firesim/firesim-software). You should clone it into
firesim-software/workloads. 

  cd firesim-software/workloads/pfa-exp
  git submodule update --init --recursive
  ./install.sh

# Benchmarks
## Baremetal PFA Tests
pfa-bare-test.json

The baremetal PFA tests act as unit tests for both the hardware and spike. It
is based on pk.

## Full linux-based PFA image
pfa-exp.json

This will create a fedora-based workload with the custom PFA-enabled linux
kernel and all the standard benchmarks.

