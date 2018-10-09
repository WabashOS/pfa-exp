CC=gcc
CFLAGS=-O2 -Wall -std=gnu99

pagerank: pagerank.c pagerank.h util.h pagerank.h
	$(CC) $(CFLAGS) -o $@ $<

data: gen-pr-data.py
	python gen-pr-data.py --nodes=2048 --binary pagerank-data-2048.bin

clean:
	rm -f pagerank
