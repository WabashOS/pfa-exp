#!/usr/bin/env python3
import pathlib
import sys
import subprocess as sp
import shutil
import re
import configparser

workdir = pathlib.Path.cwd()
marshalDir = (workdir / '../../').resolve()
fsDir = (workdir / '../../../../deploy').resolve()

def reTarget(cfgPath, newWorkload):

    cfg = configparser.ConfigParser()
    cfg.read(cfgPath)

    cfg['workload']['workloadname'] = newWorkload

    with open(cfgPath, 'w') as F:
        cfg.write(F)

def findResDir(out):
    mat = re.search("This workload's output is located in:$\n(.*)$", out, re.MULTILINE)
    return(mat.group(1))

def runWorkload(workloadName):
    print("Building workload")
    try:
        sp.run(['./marshal', 'clean', 'workloads/' + workloadName], stdout=sp.PIPE, cwd=marshalDir, check=True)
        sp.run(['./marshal', 'build', 'workloads/' + workloadName], stdout=sp.PIPE, cwd=marshalDir, check=True)
        # This is because of bug #38 in firesim-software
        sp.run(['./marshal', 'build', 'workloads/dummy.json'], stdout=sp.PIPE, cwd=marshalDir, check=True)
        sp.run(['./marshal', 'install', 'workloads/' + workloadName], stdout=sp.PIPE, cwd=marshalDir, check=True)
    except:
        print("Failed while building workload: ",workloadName)
        return False

    reTarget(fsDir / 'config_runtime.ini', workloadName)

    print("infrasetup")
    p = sp.run(["firesim", "infrasetup"], cwd=fsDir, stdout=sp.PIPE)
    if p.returncode != 0:
        print("Infrasetup workload failed:\n")
        print(p.stdout.decode('utf-8'))
        return False

    print("running")
    p = sp.run(["firesim", "runworkload"], cwd=fsDir, stdout=sp.PIPE)
    if p.returncode != 0:
        print("runworkload failed:\n")
        print(p.stdout.decode('utf-8'))
        return False

    print(p.stdout.decode('utf-8'))
    resDir = findResDir(p.stdout.decode('utf-8'))
    print("testing: ",resDir)
    p = sp.run(['./marshal', 'test', '-m', resDir, 'workloads/' + workloadName], cwd=marshalDir, stdout=sp.PIPE)
    if p.returncode != 0:
        print("results testing failed:\n")
        print(p.stdout.decode('utf-8'))
        return False

    return True

def runList(tests):
    print("Launching runfarm")
    sp.run(['firesim', 'launchrunfarm'], cwd=fsDir, check=True)
    for test in tests:
        if not runWorkload(test):
            print("Test Failure: ",test)
            break
        else:
            print("Test Success: ",test)

    sp.run("yes yes | firesim terminaterunfarm", cwd=fsDir, check=True, shell=True)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        testList = sys.argv[1:]
    else:
        testList = [ 'pfa-bare-test.json', 'pfa-br-test-real-pfa.json' ]

    shutil.copyfile(workdir / 'fs-configs/2n_runtime.ini', fsDir / 'config_runtime.ini')
    runList(testsList)
