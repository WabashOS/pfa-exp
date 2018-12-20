#!/bin/bash
# Build everything that must be build natively (does not touch cross-compilable
# stuff)

pushd linpack 
./build.sh
popd
