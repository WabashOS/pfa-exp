#!/bin/sh
pushd benchmarks/unit
echo 500K > /sys/fs/cgroup/pfa_cg/memory.max
/root/util/run_cg.sh ./unit -l
popd
