#!/usr/bin/env python3
import sys
from pathlib import Path
import re
from enum import Enum, auto
import pandas as pd
from io import StringIO

outBase = Path(sys.argv[1])

# This script works for all pflat tests, the output dir will look like:
# outBase/experiment_name/uartlog
uartPath = next(outBase.glob('*/uartlog'))
expName = str(uartPath.parts[-2])

class parseState(Enum):
    GET = auto()
    PRE_PFA = auto()
    PFA1 = auto()
    PFA2 = auto()
    PRE_LAT = auto()
    LAT1 = auto()
    LAT2 = auto()

with open(uartPath, 'r') as uartF:
    getPat = re.compile(".*RMEM Get: ([-]?\d*) cycles")

    s = parseState.GET
    stat = ""
    lat = ""
    tGet = None
    for line in uartF:
        if s == parseState.GET:
            getRes = getPat.match(line)
            if getRes:
                tGet = getRes.group(1)
                s = parseState.PRE_PFA
        elif s == parseState.PRE_PFA:
            if line == "PFA STATS\n":
                s = parseState.PFA1
        elif s == parseState.PFA1:
            stat = line    
            s = parseState.PFA2
        elif s == parseState.PFA2:
            stat += line
            s = parseState.PRE_LAT
        elif s == parseState.PRE_LAT:
            if line == "PFLAT STAT\n":
                s = parseState.LAT1
        elif s == parseState.LAT1:
            lat = line
            s = parseState.LAT2
        elif s == parseState.LAT2:
            lat += line
            break

print("t_raw_read: ", tGet)
statDF = pd.read_csv(StringIO(stat))
latDF = pd.read_csv(StringIO(lat))
finalDF = pd.concat([statDF[['t_rmem_read', 't_fault']], latDF], axis='columns')
finalDF['t_rmem_read_raw'] = tGet

print(finalDF)
with open(outBase / "result.csv", 'w') as f:
    finalDF.to_csv(f, index=False)

# This just makes it easy to automatically test that everything ran without error
(outBase / 'SUCCESS').touch()
