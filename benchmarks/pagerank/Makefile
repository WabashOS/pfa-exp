CC=gcc
CFLAGS=-O2 -Wall -std=gnu99

pagerank: pagerank.c pagerank.h util.h pagerank.h
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f pagerank
