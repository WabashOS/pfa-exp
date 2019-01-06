import subprocess as sp
import os
import sys
import argparse
import json
import datetime
from pathlib import Path
from collections import OrderedDict
import humanfriendly as hf

cgTest = Path('/sys/fs/cgroup/unified/pfa')
cgMemLimit = cgTest / 'memory.max'
cgProc = cgTest / 'cgroup.procs'

# This contains a bunch of global and state values used by various functions
class PfaState:
    def __init__(s, name, verbose=False):
        s.name = name
        s.datetime = datetime.datetime.now().strftime("%m%d%H%M")

        # Sets whether or not to print the outputs of subcommands.
        if verbose:
            s.subcmd_print = None
        else:
            s.subcmd_print = sp.DEVNULL

        # We assume the system has setup the parent cgroup ('pfa') with the desired
        # cpuset parameters. Grab them here so we can set them in the testing cgroup
        # ('pfatst')
        # ret = sp.run(['cgget', '-vnr', 'cpuset.cpus', 'pfa'], stdout=sp.PIPE, check=True)
        # s.cg_cpus = int(ret.stdout)

        # ret = sp.run(['cgget', '-vnr', 'cpuset.mems', 'pfa'], stdout=sp.PIPE, check=True)
        # s.cg_mems = int(ret.stdout)

        # The sysfs for pfa_stat is set up to support building csv's with scripts
        # pfa_stat_label holds the headers for this csv
        with open("/sys/kernel/mm/pfa_stat_label", 'r') as lbl_file:
            s.pfa_stat_lbl = lbl_file.read().strip().split(',')

    def cgReset(s, sz):
        # Cgroups can be lazy about resource accounting. If we didn't
        # delete/re-create, the next run might get charged for previous runs
        # memory.
        cgTest.rmdir()
        cgTest.mkdir()       
        
        sz = int(sz)
        if sz < 4096 and sz != -1:
            sz = 4096
        
        with open(cgMemLimit, 'w') as cgF:
            cgF.write(str(sz))

    def cgGetStat(s):
        stats = {}
        with open('/sys/kernel/mm/pfa_stat', 'r') as stat_file:
            stat_list = stat_file.read().strip().split(',')
            stat_list = [ int(i) for i in stat_list ]
            # Ordered so that we can append to CSVs consistently
            stats = OrderedDict(zip(s.pfa_stat_lbl, stat_list)) 

        return stats

    def addSelfToPFA(s):
        pid = os.getpid()
        
        # Add to cgroup
        # sp.run(['cgclassify', '-g', s.pfacg_config, str(pid)], check=True, stdout=s.subcmd_print)
        with open(cgProc, 'w') as procF:
            procF.write(str(pid))

        # Add to pfa_stat
        with open('/sys/kernel/mm/pfa_stat', 'w') as stat_file:
            stat_file.write(str(pid))

        if(os.path.isfile('/sys/kernel/mm/pfa_tsk')):
            with open('/sys/kernel/mm/pfa_tsk', 'w') as pfa_file:
                pfa_file.write(str(pid))

    # Run a single test and report statistics
    def runTest(s, bench, verbose=None):
        if verbose == None:
            printDev = s.subcmd_print
        elif verbose == True:
            printDev = None
        else:
            printDev = sp.DEVNULL

        proc = sp.Popen(bench, preexec_fn=s.addSelfToPFA, stdout=printDev)
        ret = proc.wait()
        if ret != os.EX_OK:
            print("Benchmark exited with non-zero status, aborting\n")
            raise sp.CalledProcessError(ret, bench)
        
        return s.cgGetStat()
    
    def findWorkingSz(s, bench):
        workingSzTolerance = 10
        pgsz = 4096
        # Start guessing with the "maximum resident memory size" reported by /usr/bin/time (reported in KBytes)
        ret = sp.run(['/usr/bin/time', '-f', '%M'] + bench, stderr=sp.PIPE, stdout=s.subcmd_print, check=True, universal_newlines=True)
        # All units are in terms of pages, not bytes
        upper = int((int(ret.stderr) * 1024) / pgsz)
        print("Starting with estimate: " + str(upper) + " pages")

        # binary search
        niter = 0
        # lower = upper / 2
        lower = 1 
        stat = {}
        while upper > lower:
            sz = int((upper + lower) / 2)
            s.cgReset(sz*pgsz)
            print("Running with cgroup sized: " + str(sz) + " pags (upper=" + str(upper) + " lower=" + str(lower) + ")")
            stat = s.runTest(bench)
            print("Saw " + str(stat['n_fetched']) + " faults");
            if stat['n_fetched'] == 0:
                # too big
                upper = sz - 1
            elif stat['n_fetched'] > 0:
                # too small
                lower = sz + 1

            niter = niter + 1

        # I don't expect this to run, it's just a failsafe to avoid infinite loop
        if stat['n_fetched'] > 0:
            sz = upper + 1
            s.cgReset(sz*pgsz)
            lowerStat = s.runTest(bench)
            if lowerStat['n_fetched'] > 0:
                print("Warning: Working set set larger than threshold (saw " + str(lowerStat['n_fetched']) + " faults)")

        print("Found working set size (" + str(sz) + " pages), took " + str(niter) + " iterations");
        return sz*pgsz

# Run a simple unit test
# ./pfa.py SZ BENCH [ARGS]
if __name__ == '__main__':
    sz = hf.parse_size(sys.argv[1])
    bench = sys.argv[2:]

    p = PfaState("test", verbose=True)
    p.cgReset(sz)
    stats = p.runTest(bench)
    print("Test Complete:")
    print(p.pfa_stat_lbl)
    print(stats)
    with open("test_res.csv", 'w') as resF:
        resF.write(','.join(p.pfa_stat_lbl) + "\n")
        first = True
        for v in stats.values():
            if first:
                resF.write(str(v))
                first = False
            else:
                resF.write(',' + str(v))
        resF.write("\n")
