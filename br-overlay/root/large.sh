#!/bin/sh
pushd /root/benchmarks/genome
echo 32M > /sys/fs/cgroup/pfa_cg/memory.max
/root/util/pfa_launch ./assemble little.dat
popd
cat /sys/kernel/mm/pfa_stat
