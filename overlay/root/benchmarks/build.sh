#!/bin/bash

pushd qsort
make clean
make
popd

pushd unit
make cleanall
make
popd

pushd pagerank
make
popd

pushd linpack 
./build.sh
popd
