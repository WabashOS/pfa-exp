#!/bin/bash

pushd ../benchmarks

pushd qsort
make clean
make
popd

pushd unit
make cleanall
make
popd

popd
