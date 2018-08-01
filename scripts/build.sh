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

pushd pagerank
make clean
make
popd

pushd linpack 
./build.sh
popd

popd

