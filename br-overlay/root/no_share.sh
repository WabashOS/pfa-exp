#!/bin/sh
pushd benchmarks/qsort
echo 10M > /sys/fs/cgroup/pfa_cg/memory.max
/root/util/pfa_launch ./qsort 10000000 &
/root/util/pfa_launch ./qsort 10000000 
cat /sys/kernel/mm/pfa_stat
