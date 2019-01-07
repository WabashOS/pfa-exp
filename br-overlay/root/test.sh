#!/bin/sh

reset_cg 500K
pushd /root/benchmarks/unit/
pfa_launch ./unit
popd

echo "Test Complete:"
cat /sys/kernel/mm/pfa_stat_label | tee test_res.csv
cat /sys/kernel/mm/pfa_stat | tee -a test_res.csv

# Firesim will kill everything when the first job finishes. We have to wait for
# confirmation to avoid killing other simultaneous simulations
echo "Test Done. Terminate? "
read $term
