#!/bin/sh

RES_FILE=../test_res.csv

while getopts ":hi" opt; do
  case ${opt} in
    i )
      INTERACTIVE=1
      ;;
    \? ) echo "Usage: cmd [-i]"
      echo -e "\t-i interactive: Wait for user input before terminating test (useful on FireSim to avoid premature simulation termination)."
      ;;
  esac
done

reset_cg 500K
pushd /root/benchmarks/unit/
pfa_launch ./unit
popd

echo "Test Complete:"
cat /sys/kernel/mm/pfa_stat_label | tee $RES_FILE
cat /sys/kernel/mm/pfa_stat | tee -a $RES_FILE

# Firesim will kill everything when the first job finishes. We have to wait for
# confirmation to avoid killing other simultaneous simulations
if [ $INTERACTIVE ]; then
  echo "Test Done. Terminate? "
  read $term
fi
