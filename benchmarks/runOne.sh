#!/bin/sh
# Usage:
# ./runOne.sh args.cfg
# see qsort.cfg for an example of args.cfg

source $PWD/$1
((m75 = (3*$workSz) / 4))
((m50 = $workSz /2))
((m25 = $workSz /4))

echo "Testing: $CMD $ARGS"

reset_cg $m25
mytime pfa_launch $CMD $ARGS

cat /sys/kernel/mm/pfa_stat_label
cat /sys/kernel/mm/pfa_stat
