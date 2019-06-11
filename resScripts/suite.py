#!/usr/bin/env python3

import sys
import re
import time
import shutil
import csv
import subprocess as sp
from pathlib import Path

# csv doesn't use ordered dicts so we have to save this here to get a readable csv output
csvHeader = ['Config', 'Benchmark', 'Args', 'MemFrac', 'MemSz', 'TotalRuntime', 't_run',
        't_bookkeeping', 't_rmem_write', 't_rmem_read', 'n_fault', 't_fault', 'n_fault_fetched',
        'n_swapfault', 'n_pfa_fault', 'n_early_newq', 'n_evicted', 'n_fetched',
        'n_kpfad', 'n_kpfad_fetched', 't_kpfad']

# firesim output directory
outBase = Path(sys.argv[1])
runName = re.search('.*-pfa-suite-(.*)$', outBase.name).group(1)

# Destination for results
resDir = Path(__file__).parent / '../pfa-results/raw' / runName / time.strftime("%Y-%m-%d--%H-%M-%S", time.gmtime())
resDir.mkdir(parents=True)

# Directories containing experimental results
expDirs = [ d for d in outBase.glob('pfa-suite-*') if not re.search('memblade|blank', str(d)) ]

# These should all be the same, it's collected just for posterity
shutil.copy(str(expDirs[0] / 'config.gz'), str(resDir))
sp.call(['gunzip', 'config.gz'], cwd=str(resDir))

csvRes = []
for exp in expDirs:
    csvPaths = exp.glob('*.csv')
    
    for p in csvPaths:
        with open(str(p), 'r') as csvF:
            res = csv.DictReader(csvF)
            csvRes += list(res)

for r in csvRes:
    r['Config'] = runName

with open(str(resDir / 'results.csv'), 'w') as resF:
    writer = csv.DictWriter(resF, fieldnames=csvHeader)
    writer.writeheader()
    for res in csvRes:
        writer.writerow(res)
