#!/bin/sh
pushd benchmarks/unit
reset_cg 500K
pushd /root/benchmarks/unit/
pfa_launch ./unit -l
popd
