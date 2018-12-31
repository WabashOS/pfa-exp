#!/usr/bin/env python3
import sys
from pathlib import Path
import re

outBase = Path(sys.argv[1])

# This script works for all pflat tests, the output dir will look like:
# outBase/experiment_name/uartlog
uartPath = next(outBase.glob('*/uartlog'))
expName = str(uartPath.parts[-2])

with open(str(uartPath), 'r') as uartF:
    trapPat = re.compile("Trap took ([-]?\d*) cycles")
    e2ePat = re.compile("End-To-End Took ([-]?\d*) cycles")
    # Set to None to ensure an error occurs if the output doesn't match
    tCycles = None
    eCycles = None
    for line in uartF:
        trapRes = trapPat.match(line)
        e2eRes = e2ePat.match(line)
        if trapRes:
            tCycles = trapRes.group(1)
            
        if e2eRes:
            eCycles = e2eRes.group(1)
        
with open(str(outBase / (expName + '.csv')), 'w') as res:
    res.write('expName,trapCycles,e2eCycles\n')
    res.write(','.join([expName, tCycles, eCycles]) + '\n')

# This just makes it easy to automatically test that everything ran without error
(outBase / 'SUCCESS').touch()
