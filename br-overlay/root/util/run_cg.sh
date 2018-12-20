#!/bin/bash

echo $$ > /sys/fs/cgroup/pfa_cg/cgroup.procs
exec $@
