#!/bin/bash
# Setup this repo to work with firesim-software. You should check this repo out into firesim-software/workloads/ and then run this script. You can then run the pfa experiments. e.g. "./sw_manager.py test workloads/pfa-bare-test.json".

pushd ../
ln -s pfa-exp/wl-configs/*.json .
popd

cp fs-configs/2n_runtime.ini ../../../../../deploy/config_runtime.ini
cp fs-configs/config_hwdb.ini ../../../../../deploy/
cp fs-configs/config_build_recipes.ini ../../../../../deploy/

./build.sh
