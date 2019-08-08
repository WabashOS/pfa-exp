#!/usr/bin/env python3

import sys
import re
import time
import shutil
import csv
import subprocess as sp
import configparser
from pathlib import Path

def getGitCommit(path):
    return sp.check_output(['git', 'rev-parse', 'HEAD'], cwd=path).decode("utf-8").strip()
    
fsTopDir = (Path(__file__) / '../../../../../../').resolve()
pfaWorkDir = (Path(__file__) / '../../').resolve()

# firesim output directory
outBase = Path(sys.argv[1])
parsedOutBase = re.search('(.*)-pfa-suite-(.*)$', outBase.name)
runDate = parsedOutBase.group(1)
runName = parsedOutBase.group(2)

# Destination for results
resDir = pfaWorkDir / 'pfa-results/raw' / runName / runDate
if resDir.exists():
    print("Results directory already exists!")
    print(resDir)
    sys.exit()

resDir.mkdir(parents=True)

# Directories containing experimental results
expDirs = [ d for d in outBase.glob('pfa-suite-*') if not re.search('memblade|blank', str(d)) ]

# Linux Configuration
shutil.copy(str(expDirs[0] / 'config.gz'), str(resDir))
sp.call(['gunzip', 'config.gz'], cwd=str(resDir))
linuxCfg = configparser.ConfigParser()
with open(resDir / 'config', 'r') as cfgF:
    linuxCfg.read_string('[root]\n' + cfgF.read())
linuxCfg = linuxCfg['root']

# FireSim Configs
runtimeCfg = configparser.ConfigParser()
runtimeCfg.read(fsTopDir / 'deploy' / 'config_runtime.ini')
hwdbCfg = configparser.ConfigParser()
hwdbCfg.read(fsTopDir / 'deploy' / 'config_hwdb.ini')

# Global configuration information for this run
runCfg = {
        'hwconfig' : runtimeCfg['targetconfig']['defaulthwconfig'],
        'agfi' : hwdbCfg[runtimeCfg['targetconfig']['defaulthwconfig']]['agfi'],
        'linklatency' : runtimeCfg['targetconfig']['linklatency'],
        'expName' : runName,
        'dateTime' : runDate,
        'qDepth' : linuxCfg['CONFIG_PFA_NEWQ_SIZE'],
        'kpfad' : linuxCfg.get('CONFIG_PFA_KPFAD', 'n'),
        'pfaEm' : linuxCfg.get('CONFIG_PFA_EM', 'n'),
        'membladeEm' : linuxCfg.get('CONFIG_MEMBLADE_EM', 'n'),
        'debugMode' : linuxCfg.get('CONFIG_PFA_DEBUG', 'n'),
        'verboseMode' : linuxCfg.get('CONFIG_PFA_VERBOSE', 'n'),
        'linuxCommit' : getGitCommit(pfaWorkDir / 'riscv-linux'),
        'pfaCommit' : getGitCommit(pfaWorkDir)
        }

csvRes = []
for exp in expDirs:
    csvPaths = exp.glob('*.csv')
    
    for p in csvPaths:
        with open(str(p), 'r') as csvF:
            res = csv.DictReader(csvF)
            csvRes += list(res)

for r in csvRes:
    r.update(runCfg)

with open(str(resDir / 'results.csv'), 'w') as resF:
    writer = csv.DictWriter(resF, fieldnames=csvRes[0].keys())
    writer.writeheader()
    for res in csvRes:
        writer.writerow(res)
