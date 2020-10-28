#!/bin/sh
pushd benchmarks/unit
reset_cg 500K
pushd /root/benchmarks/unit/
pfa_launch ./unit -l
popd

cat /sys/kernel/mm/pfa_stat_label
cat /sys/kernel/mm/pfa_stat
