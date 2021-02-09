#!/bin/bash
# Setup this repo to work with firesim-software. You should check this repo out into firesim-software/workloads/ and then run this script. You can then run the pfa experiments. e.g. "./sw_manager.py test workloads/pfa-bare-test.json".

SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

cd $SCRIPTDIR

pushd ../
ln -s pfa-exp/wl-configs/*.json .
popd

if [[ -d ../../../../deploy ]]; then
    cp fs-configs/pfa_runtime.ini ../../../../deploy/config_runtime.ini
    cp fs-configs/config_hwdb.ini ../../../../deploy/
    cp fs-configs/config_build_recipes.ini ../../../../deploy/
    cp fs-configs/config_build.ini ../../../../deploy/
fi

pushd linux-configs/patches
./patchCfg.py ../br *.patch
./patchCfg.py ../fed *.patch
popd

pushd ../dummy
./build.sh
popd

./build.sh
