import subprocess as sp
import os
import sys
import argparse
import json
import datetime
from collections import OrderedDict

# This contains a bunch of global and state values used by various functions
class PfaState:
    def __init__(s, name):
        s.name = name
        s.datetime = datetime.datetime.now().strftime("%m%d%H%M")
        s.pfacg_path = "pfa/pfatst"
        s.pfacg_config = "memory,cpuset:" + s.pfacg_path

        # Set this to None to print out sub-command outputs, sp.DEVNULL will
        # supress subcommand outputs s.subcmd_print = None
        s.subcmd_print = sp.DEVNULL

        # We assume the system has setup the parent cgroup ('pfa') with the desired
        # cpuset parameters. Grab them here so we can set them in the testing cgroup
        # ('pfatst')
        ret = sp.run(['cgget', '-vnr', 'cpuset.cpus', 'pfa'], stdout=sp.PIPE, check=True)
        s.cg_cpus = int(ret.stdout)

        ret = sp.run(['cgget', '-vnr', 'cpuset.mems', 'pfa'], stdout=sp.PIPE, check=True)
        s.cg_mems = int(ret.stdout)

        # The sysfs for pfa_stat is set up to support building csv's with scripts
        # pfa_stat_label holds the headers for this csv
        with open("/sys/kernel/mm/pfa_stat_label", 'r') as lbl_file:
            s.pfa_stat_lbl = lbl_file.read().strip().split(',')

    def cgReset(s, sz):
        s.cgDelete()
        sp.run(['cgcreate', "-g", s.pfacg_config], check=True)
        sp.run(['cgset', '-r', 'cpuset.cpus=' + str(s.cg_cpus), s.pfacg_path], check=True)
        sp.run(['cgset', '-r', 'cpuset.mems=' + str(s.cg_mems), s.pfacg_path], check=True)
        s.cgSetMem(sz)

    def cgDelete(s):
        sp.run(['cgdelete', s.pfacg_config], stdout=s.subcmd_print, stderr=sp.DEVNULL)

    def cgSetMem(s, sz):
        sz = int(sz)
        if sz < 4096 and sz != -1:
            sz = 4096
        
        sp.run(['cgset', '-r', 'memory.limit_in_bytes=' + str(sz), s.pfacg_path], check=True)

        # cgset seems to return SUCCESS, even if it failed, the only way to check
        # is to see if the parameter was set correctly. Note that the memory limit
        # always rounds down to the nearest multiple of a page size.
        ret = sp.run(['cgget', '-vnr', 'memory.limit_in_bytes', s.pfacg_path], stdout=sp.PIPE, check=True)
        npage_got = int(int(ret.stdout) / 4096)
        npage_req = int(sz / 4096)
        if(npage_got != npage_req and sz != -1):
            print("Failed to set cgroup value: expected: " + str(npage_req*4096) + " got: " + str(npage_got*4096))
            return False

        return True

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
        sp.run(['cgclassify', '-g', s.pfacg_config, str(pid)], check=True, stdout=s.subcmd_print)

        # Add to pfa_stat
        with open('/sys/kernel/mm/pfa_stat', 'w') as stat_file:
            stat_file.write(str(pid))

        # XXX This hasn't been tested because fedora doesn't work on spike
        if(os.path.isfile('/sys/kernel/mm/pfa_tsk')):
            with open('/sys/kernel/mm/pfa_tsk', 'w') as pfa_file:
                pfa_file.write(str(pid))

    # Run a single test and report statistics
    def runTest(s, bench):
        proc = sp.Popen(bench, preexec_fn=s.addSelfToPFA, stdout=sp.DEVNULL)
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
        lower = upper / 2
        sz = lower 
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
