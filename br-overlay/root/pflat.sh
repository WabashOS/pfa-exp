#!/bin/sh
pushd benchmarks/unit
echo 500K > /sys/fs/cgroup/pfa_cg/memory.max
pushd /root/benchmarks/unit/
/root/util/pfa_launch ./unit -l
popd
