#!/bin/bash

pushd ../benchmarks

pushd qsort
make
popd

pushd unit
make
popd

popd
