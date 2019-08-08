#!/usr/bin/env python3
"""
Usage:
    ./patchCfg.py /path/to/BASE path/to/DERIVED.patch

Apply a patch to a base linux config (storing the result in ../BASE-DERIVED). The base
config should be a complete linux configuration file. The patch contains one
option per line (unlike in the real config, each option must be explicit
(CONFIG_EXAMPLE=foo), and not a comment. Each line in the patch will override
the corresponding option in the base config. It is best to include any option
that might matter instead of assuming the base is a certain way. The intention
is to set things in the PFA and MEMBLADE sections, overriding the
CONFIG_CMDLINE or other options might not be a good idea.
"""

import sys
import os
import re

def applyPatch(basePath, patchPath):
    patchSplit = os.path.splitext(patchPath)
    if patchSplit[1] is None:
        sys.exit("Patch file must have an extension (e.g. '.patch')")

    dstPath = "../" + os.path.basename(basePath) + "-" + patchSplit[0]

    opts = []
    with open(patchPath, 'r') as patchF:
        pat = re.compile("(.*)=.*")
        for line in patchF:
            if line[0] == '#' or line[0] == '\n':
                continue

            match = pat.match(line)
            if not match:
                sys.exit("Couldn't parse line in patch: " + line)
            opt = match.group(1)
            patchPattern = re.compile("^# " + opt + " is not set" + "$|^" + opt + "=.*$")
            opts.append( (patchPattern, line) )

    with open(basePath, 'r') as baseF:
        with open(dstPath, 'w') as dstF:
            for baseLine in baseF:
                matched = False
                for (pat,patchLine) in opts:
                    if pat.match(baseLine):
                        dstF.write(patchLine)
                        matched = True
                        break
                if not matched:
                    dstF.write(baseLine)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Incorrect arguments. Usage:")
        print(__file__ + " baseConfig patch")
        sys.exit()

    basePath = sys.argv[1]
    patchPaths = sys.argv[2:]

    for p in patchPaths:
        applyPatch(basePath, p)
