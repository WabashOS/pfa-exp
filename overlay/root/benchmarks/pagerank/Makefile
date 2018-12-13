CC=gcc
CFLAGS=-O2 -Wall -std=gnu99

all: pagerank data

pagerank: pagerank.c pagerank.h util.h pagerank.h
	$(CC) $(CFLAGS) -o $@ $<

data: pagerank-data-2048.bin

pagerank-data-2048.bin: gen-pr-data.py
	python gen-pr-data.py --nodes=2048 --binary pagerank-data-2048.bin

clean:
	rm -f pagerank

cleanall: clean
	rm -f pagerank-data-2048.bin
