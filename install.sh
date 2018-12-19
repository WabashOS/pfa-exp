#!/bin/bash
# Setup this repo to work with firesim-software. You should check this repo out into firesim-software/workloads/ and then run this script. You can then run the pfa experiments. e.g. "./sw_manager.py test workloads/pfa-bare-test.json".

pushd ../
ln -s pfa-exp/pfa-base.json .
ln -s pfa-exp/pfa-exp.json .
ln -s pfa-exp/pfa-bare-test.json .
popd

./build.sh
