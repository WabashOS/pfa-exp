#!/bin/bash
# Cross compile everything that supports cross-compilation

pushd qsort
make clean
make CROSS=riscv
popd

pushd unit
make cleanall
make CROSS=riscv
popd

pushd pagerank
make CROSS=riscv
popd
