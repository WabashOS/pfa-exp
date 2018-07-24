#!/usr/bin/env python3
import subprocess as sp

pfacg_path = "pfa/pfatst"

def cgReset():
    cgDelete()
    sp.run(['cgcreate', "-g", 'memory:' + pfacg_path], check=True)

def cgDelete():
    sp.run(['cgdelete', 'memory:' + pfacg_path], stdout=sp.DEVNULL, stderr=sp.DEVNULL)

def cgSetMem(sz):
    sz = int(sz)
    if sz < 4096 and sz != -1:
        sz = 4096
    
    sp.run(['cgset', '-r', 'memory.limit_in_bytes=' + str(sz), pfacg_path], check=True)

    # cgset seems to return SUCCESS, even if it failed, the only way to check
    # is to see if the parameter was set correctly. Note that the memory limit
    # always rounds down to the nearest multiple of a page size.
    ret = sp.run(['cgget', '-vnr', 'memory.limit_in_bytes', pfacg_path], stdout=sp.PIPE, check=True)
    npage_got = int(int(ret.stdout) / 4096)
    npage_req = int(sz / 4096)
    if(npage_got != npage_req and sz != -1):
        print("Failed to set cgroup value: expected: " + str(npage_req*4096) + " got: " + str(npage_got*4096))
        return False

    return True

def cgRun(bench):
    return sp.run(['cgexec', '-g', 'memory:' + pfacg_path] + bench, check=True, stdout=sp.DEVNULL)

def cgGetStat():
    ret = sp.run(['cgget', '-vnr', 'memory.stat', pfacg_path], stdout=sp.PIPE, check=True, universal_newlines=True)

    stats = {}
    for line in ret.stdout.splitlines():
        vals = line.strip().split(" ")
        stats[vals[0]] = int(vals[1])

    return stats

workingSzTolerance = 50
def findWorkingSz(bench):
    # Start guessing with the "maximum resident memory size" reported by /usr/bin/time (reported in KBytes)
    ret = sp.run(['/usr/bin/time', '-f', '%M'] + bench, stderr=sp.PIPE, stdout=sp.DEVNULL, check=True, universal_newlines=True)
    upper = int(ret.stderr) * 1024
    print("Starting with estimate: " + str(upper))

    # Now binary search
    niter = 0
    lower = upper / 2
    sz = lower 
    stat = {}
    while upper - lower > 4096:
        sz = int((upper + lower) / 2)
        cgReset()
        cgSetMem(sz)
        print("Running with cgroup sized: " + str(sz))
        cgRun(bench)
        stat = cgGetStat()
        print("Saw " + str(stat['total_pgmajfault']) + " faults");
        if stat['total_pgmajfault'] == 0:
            # too big
            upper = sz - 1
        elif stat['total_pgmajfault'] > workingSzTolerance:
            # too small
            lower = sz + 1 
        else:
            # Juuuust right
            break

        niter = niter + 1

    # I don't expect this to run, it's just a failsafe to avoid infinite loop
    if stat['total_pgmajfault'] > workingSzTolerance:
        print("Warning: Working set set larger than threshold")

    print("Found working set size, took " + str(niter) + " iterations");
    return sz

cgReset()
sz = findWorkingSz(['./benchmarks/unit/unit', '-s', '100000000'])
print("Working set sized: " + str(sz))
cgDelete()

