# CC=riscv64-unknown-linux-gnu-gcc
CC=gcc
CFLAGS=-O2 -Wall
OBJDUMP=riscv64-unknown-linux-gnu-objdump

PROGRAMS = memblade-bmark memblade-lat pagerank-local pagerank-remote load-memblade

default: $(addsuffix .riscv,$(PROGRAMS))

dumps: $(addsuffix .dump,$(PROGRAMS))

%.dump: %.riscv
	$(OBJDUMP) -D $< > $@

%.riscv: %.o
	$(CC) $< $(LDFLAGS) -o $@

memblade-bmark.o: memblade-bmark.c memblade.h util.h barrier.h
	$(CC) $(CFLAGS) -c $< -o $@

memblade-lat.o: memblade-lat.c memblade.h util.h barrier.h
	$(CC) $(CFLAGS) -c $< -o $@

pagerank-local.o: pagerank-local.c pagerank.h util.h
	$(CC) $(CFLAGS) -c $< -o $@

pagerank-remote.o: pagerank-remote.c pagerank.h memblade.h util.h barrier.h
	$(CC) $(CFLAGS) -c $< -o $@

load-memblade.o: load-memblade.c memblade.h util.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o
