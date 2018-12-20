#!/bin/sh
pushd /root/benchmarks/qsort
echo 5M > /sys/fs/cgroup/pfa_cg/memory.max
/root/util/pfa_launch ./qsort 10000000
popd
cat /sys/kernel/mm/pfa_stat
