#!/bin/sh
echo 500K > /sys/fs/cgroup/pfa_cg/memory.max
pushd /root/benchmarks/unit/
/root/util/pfa_launch ./unit
popd
cat /sys/kernel/mm/pfa_stat
