#!/bin/sh
# Usage:
# ./runSuite.sh args.cfg
# see qsort.cfg for an example of args.cfg

source $PWD/$1
((m75 = (3*$workSz) / 4))
((m50 = $workSz /2))
((m25 = $workSz /4))

RES_PATH=/root/$(basename $CMD)_res.csv

echo "Results in: $RES_PATH" 
echo "Testing: $CMD $ARGS"
echo -n "Benchmark,Args,MemFrac,MemSz,TotalRuntime," | tee $RES_PATH
cat /sys/kernel/mm/pfa_stat_label | tee -a $RES_PATH

echo "Full Size"
echo -n "$CMD,$ARGS,1.00,$workSz," >> $RES_PATH
reset_cg $workSz
mytime pfa_launch $CMD $ARGS 2>> $RES_PATH
cat /sys/kernel/mm/pfa_stat >> $RES_PATH
tail -n 1 $RES_PATH
sync

echo "75%"
echo -n "$CMD,$ARGS,0.75,$m75," >> $RES_PATH
reset_cg $m75
mytime pfa_launch $CMD $ARGS 2>> $RES_PATH
cat /sys/kernel/mm/pfa_stat >> $RES_PATH
tail -n 1 $RES_PATH
sync

echo "50%"
echo -n "$CMD,$ARGS,0.50,$m50," >> $RES_PATH
reset_cg $m50
mytime pfa_launch $CMD $ARGS 2>> $RES_PATH
cat /sys/kernel/mm/pfa_stat >> $RES_PATH
tail -n 1 $RES_PATH
sync

echo "25%"
echo -n "$CMD,$ARGS,0.25,$m25," >> $RES_PATH
reset_cg $m25
mytime pfa_launch $CMD $ARGS 2>> $RES_PATH
cat /sys/kernel/mm/pfa_stat >> $RES_PATH
tail -n 1 $RES_PATH
sync

# Firesim will kill everything when the first job finishes. We have to wait for
# confirmation to avoid killing other simultaneous simulations
echo "Test Done. Terminate? "
read $term
