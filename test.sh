#!/bin/bash
shopt -s extglob

# This tests the core PFA functionalities IN FUNCTIONAL SIMULATION ONLY. This does
# not test actual firesim behavior.

pushd ../../

if [ ! -e marshal ]; then
  echo "Can't find marshal command. This test assume's it's run from firesim-software/workloads/pfa-exp."
  exit 1
fi

if [ ! -e workloads/pfa-bare-test.json ]; then
  echo "Please run ./install.sh first"
  exit 1
fi

SUITE_PASS=true

# Actual tests begin
echo "Running Qemu-only Tests"
QEMU_TESTS="@(pfa-br-test-em-pfa|pfa-br-test-em-mb)"
./marshal clean workloads/$QEMU_TESTS.json
./marshal test workloads/$QEMU_TESTS.json
if [ ${PIPESTATUS[0]} != 0 ]; then
  echo "Failure"
  SUITE_PASS=false
else
  echo "Success"
fi

echo "Running bare-metal Tests"
BARE_TESTS="@(pfa-bare-test)"
./marshal clean workloads/$BARE_TESTS.json
./marshal test -s workloads/$BARE_TESTS.json
if [ ${PIPESTATUS[0]} != 0 ]; then
  echo "Failure"
  SUITE_PASS=false
else
  echo "Success"
fi

echo "Running Spike-only Tests"
SPIKE_TESTS="@(pfa-br-test-real-pfa)"
./marshal -i clean workloads/$SPIKE_TESTS.json
./marshal -i test -s workloads/$SPIKE_TESTS.json
if [ ${PIPESTATUS[0]} != 0 ]; then
  echo "Failure"
  SUITE_PASS=false
else
  echo "Success"
fi

popd

if [ $SUITE_PASS = false ]; then
  echo "FAILURE: Some tests failed"
  exit 1
else
  echo "SUCCESS: Full test success"
  exit 0
fi
