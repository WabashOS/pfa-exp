= pflat =
These tests measure the latency of a page fault and trap. This uses the unit
test benchmark and requires the "CONFIG_PFLAT" option in the kernel.

Note: This test is a little racey and unreliable. Sometimes you have to run it
multiple times to get it to work. The root cause is that we can't always
guarantee that the last page that was evicted is still evicted when we run the
test or ever really was (lots of outs in the paging system to cancel an
eviction). Anyway, it either works or it doesn't (you'll get a 0 for trap start
time and a very small end-to-end time if it fails).

== configurations ==
* manual - intended for manual interaction and testing. Setup for single node
           in full emulation mode.
* mb-em - Automated test. Emulate memory blade.
* mb-real - Automated test. Real memory blade.
* pfa - Automated test. Real memblade and uses PFA. Note that the trap time
        won't be meaningful here because the pfa doesn't experience a trap.
