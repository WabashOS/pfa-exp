Setting up fedora for experiments (based on riscv-fedora grabbed circa july 2018).

# Basic packages:
Run ./bootstrap_fedora.sh which will do everything that I've gotten around to automating.

# Linpack Dependencies:
For linpack, we use the hpl benchmark (in pfa-exp/benchmarks) which has some challening dependencies. None of this would be necessary if Fedora had a working mpich package.

Problem 1: The mpich rpm in the repos dependes on libmpi.so.12 which it
actually includes, but it doesn't seem to realize it.

Solution: Download the package manually and install using rpm -ivh --nodeps to
skip the dependency check.

Problem 2: mpich installs itself in a weird place. I think this is because it's trying to be polite and support multiple versions of MPI on one system? I dunno, stupid HPC crap.

Solution: After installing mpich, you need to symlimk all the .so's from /lib64/mpich/lib/ to /lib64/ and everything should work.
