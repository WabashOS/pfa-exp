#!/usr/bin/env python3
import sys
from pathlib import Path
import re
import csv

outBase = Path(sys.argv[1])

def fromUart(uartPath):

    with open(str(uartPath), 'r') as uartF:
        res = [] 
        found = False
        pat = re.compile("Test Complete:")
        for line in uartF:
            # uartlogs on firesim have lots of extra ^M characters, try to ignore them
            line = line.rstrip()
            if line == "":
                continue

            if not found:
                if pat.match(line):
                    found = True
                    print("found")
            else:
                print(line)
                res.append(line)
                if len(res) == 2:
                    break
    return next(csv.DictReader(res))

def fromFile(csvPath):
    with open(str(csvPath), 'r') as csvF:
        return next(csv.DictReader(csvF))

if (outBase / 'pfa-fed-test-client').exists():
    stats = fromFile(outBase / 'pfa-fed-test-client' / 'test_res.csv')
elif (outBase / 'pfa-br-test-client').exists():
    stats = fromUart(outBase / 'pfa-br-test-client' / 'uartlog')
else:
    print("Failure: Couldn't find results directory")
    sys.exit(1)

print("Stats: ")
print(stats)

if int(stats['n_fetched']) <= 10:
    print("Failure: Didn't seem to fetch enough pages: " + str(stats['n_fetched']))
else:
    print("Passed")
    (outBase / 'SUCCESS').touch()
    with open(str(outBase / 'test_res.csv'), 'w') as sucF:
        writer = csv.DictWriter(sucF, fieldnames=stats.keys())
        writer.writeheader()
        writer.writerow(stats)
