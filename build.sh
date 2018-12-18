#!/bin/bash
set -e

# Spike
echo "Building pfa spike"
LOCAL_INSTALL=$PWD/spike-install
mkdir -p $LOCAL_INSTALL

if [ ! -d riscv-isa-sim/build ]; then
  mkdir riscv-isa-sim/build
  pushd riscv-isa-sim/build
  ../configure --with-fesvr=$RISCV --prefix=$LOCAL_INSTALL
  popd
fi

pushd riscv-isa-sim/build
make -j16
make install
popd

# Bare-metal unit test
echo "Building bare-metal pfa tests"
if [ ! -d pfa-bare-test/build ]; then
  mkdir pfa-bare-test/build
  pushd pfa-bare-test/build
  ../configure --prefix=$RISCV --host=riscv64-unknown-elf
  popd
fi

pushd pfa-bare-test/build
make -j16
popd
