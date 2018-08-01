#!/usr/bin/env python3
import os
import sys
import argparse
import json
import pfa
import datetime
import pprint
import csv
import time

scale_factors = [1.0, 0.75, 0.5, 0.25]

def handleReset(args, exp, benchmarks):
    if args.benchmark != None:
        sz = int(0.75 * benchmarks[args.benchmark][1])
    else:
        sz = args.size

    print("Resetting control group to to size " + str(sz))
    exp.cgReset(sz)
    sys.exit(os.EX_OK)

def handleRun(args, exp, benchmarks):
    if args.command != None:
        command = args.command.split()
    elif args.benchmark in benchmarks:
        command = benchmarks[args.benchmark][0]
    else:
        print("'" + args.benchmark + "': no such benchmark")
        return

    print("running: " + " ".join(command))
    stat = exp.runTest(command, verbose=True)
    print(exp.name + ":\n" + pprint.pformat(stat))

    
def handleSize(args, exp, benchmarks):
    if args.command != None:
        command = args.command.split()
    elif args.benchmark in benchmarks:
        command = benchmarks[args.benchmark][0]
    else:
        print("'" + args.benchmark + "': no such benchmark")
        return

    print("Finding working set size for: " + " ".join(command))
    sz = exp.findWorkingSz(command)
    print("Size: " + str(sz))

    if args.name != None:
        benchName = args.name
    else:
        benchName = os.path.basename(command[0])

    if args.output != None:
        try:
            with open(args.output, 'r') as benchFile:
                oldBenchs = json.load(benchFile)
        except FileNotFoundError:
            oldBenchs = {}

        oldBenchs[benchName] = (command, sz)
        with open(args.output, 'w') as benchFile:
            json.dump(oldBenchs, benchFile, indent=4)

def handleLsbench(args, exp, benchmarks):
    print("Benchmarks:")
    for name, desc in benchmarks.items():
        print(name + ":")
        print("Command: " + " ".join(desc[0]))
        print("Working Set: " + str(desc[1]) + " bytes")
   
def handleRunSte(args, exp, benchmarks):
    suiteStart = time.time()
    if args.output != None:
        resPath = args.output
    else:
        resPath = './results_' + exp.name + '.csv'

    if args.benchmark != None:
        suite_names = args.benchmark.split(",")
        suite = { k: benchmarks[k] for k in suite_names }
    else:
        suite = benchmarks

    header = ['datetime', 'run', 'benchmark', 'command', 'size'] + exp.pfa_stat_lbl
    results = []
    for bench,desc in suite.items():
        command = desc[0]
        baseSz = desc[1]
        for scale in scale_factors:
            runStart = time.time()
            sz = int(baseSz*scale)
            print("Running " + bench + " at scale-factor: " + str(scale))
            exp.cgReset(sz)
            stat = exp.runTest(command)
            runTime = time.time() - runStart
            results.append([exp.datetime, exp.name, bench, " ".join(command), sz] + list(stat.values())) 
            print("Took " + str(runTime) + " seconds")

    if os.path.exists(resPath):
        with open(resPath, 'a', newline='') as resFile:
            writer = csv.writer(resFile)
            writer.writerows(results)
    else:
        with open(resPath, 'w', newline='') as resFile:
            writer = csv.writer(resFile)
            writer.writerow(header)
            writer.writerows(results)

    print("Run successful, results written to: " + resPath)
    print("Took " + str(time.time() - suiteStart) + "seconds")

# Parse command line arguments and call the appropriate function to handle the
# commands.
def main():
    parser = argparse.ArgumentParser(description=
        'Run a pfa command. You may provide a pre-configured benchmark file '
        '(typically generated using the "size" command). If no benchmark file is '
        'provided, the tool will default to "./test.json".i')
    parser.add_argument('-b', '--benchfile', default='./test.json')
    parser.add_argument('-n', '--name', help="Name to use "
            "for this session, will be used in various outputs (called NAME in "
            "this documentation). Defaults to date/time 'mmddHHMM'")
    subparsers = parser.add_subparsers(title='Available sub-commands:')

    # 'reset' command
    reset_parser = subparsers.add_parser('reset', help='Reset the testing cgroup. Only needed for manual testing.')
    reset_parser.set_defaults(func=handleReset)
    reset_parser.add_argument('-s', '--size', default = -1, type=int,
            help='Optional size (in byte) to initialize the cgroup memory limit to.')
    reset_parser.add_argument('-b', '--benchmark', help="Set the"
           " cgroup up for the provided benchmark BENCH (see lsbench command)."
           " Will set the memory to 75%% of working set for that benchmark.")

    # 'run' command
    run_parser = subparsers.add_parser('run', help=
       'Run the provided benchmark or command. Must call "reset" first. Only'
       ' needed for manual testing. Only runs the benchmark, doesn\'t collect any'
       ' stats or anything.')
    run_parser.set_defaults(func=handleRun)
    run_parser.add_argument('-b', '--benchmark', default = 'unit',
            help='Use the provided benchmark (see lsbench command).')
    run_parser.add_argument('-c', '--command', help=
            'Use the provided command. If the command has arguments, the entire '
            'command line must be enclosed in quotes.')

    # 'size' command
    sz_parser = subparsers.add_parser('size', help=
        'Find the working set size for the provided benchmark or command.')
    sz_parser.set_defaults(func=handleSize)
    sz_parser.add_argument('-b', '--benchmark', default= 'unit', help=
            'Use the provided benchmark BENCH (see lsbench command).')
    sz_parser.add_argument('-c', '--command', help=
            'Use the provided command. If the command has arguments, the entire '
            'command line must be enclosed in quotes.')
    sz_parser.add_argument('-o', '--output', help=
            'Append the result to the provided benchmark file (or create a new one).')
    sz_parser.add_argument('-n', '--name', help=
            'Name to use for this benchmark (only meaningful in combination with -o)')

    # 'lsbench' command
    lsbench_parser = subparsers.add_parser('lsbench', help='List all available benchmarks')
    lsbench_parser.set_defaults(func=handleLsbench)

    # 'runsuite' command
    runste_parser = subparsers.add_parser('runsuite', help='Run all benchmarks in a suite')
    runste_parser.set_defaults(func=handleRunSte)
    runste_parser.add_argument('-o', '--output', help='Append the result (as '
            'csv) to the provided results file. If the output file doesn\'t '
            'exist one will be created with the appropriate column headers. '
            'Defaults to ./results_NAME.csv')
    runste_parser.add_argument('-b', '--benchmark', help=
            'Run only the provided benchmarks (comma sepparated list of names).')
    args = parser.parse_args()

    # # 'pflat' command
    # runste_parser = subparsers.add_parser('pflat', help='Measure a single page-fault in detail.')
    # runste_parser.set_defaults(func=handlePflat)
    
    if args.name == None:
        # Used to create unique names (as needed)
        dtime = datetime.datetime.now()
        name = dtime.strftime("%m%d%H%M")
    else:
        name = args.name

    # Experiment state
    exp = pfa.PfaState(name)

    # Load benchmark file
    with open(args.benchfile, 'r') as bfile:
        benchmarks = json.load(bfile)

    args.func(args, exp, benchmarks)

    sys.exit(os.EX_OK)

main()
