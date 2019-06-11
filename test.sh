#!/bin/bash

# This tests the core PFA functionalities IN FUNCTIONAL SIMULATION ONLY. This does
# not test actual firesim behavior.

pushd ../../

if [ ! -e marshal ]; then
  echo "Can't find marshal command. This test assume's it's run from firesim-software/workloads/pfa-exp."
fi

if [ ! -e workloads/pfa-bare-test.json ]; then
  echo "Please run ./install.sh first"
fi

# Actual tests begin
./marshal test -s workloads/pfa-bare-test.json
if [ ${PIPESTATUS[0]} != 0 ]; then
  echo "Bare metal test failure (pfa-bare-test.json)"
  exit 1
fi

echo -e "\n\nSUCCESS"
