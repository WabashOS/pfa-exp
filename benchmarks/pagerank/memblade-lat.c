#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "memblade.h"
#include "util.h"
#include "barrier.h"

int pgsize, pgwords;

void setup_page_read(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_PAGE_READ);
	rmem_set_dst_addr(iomem, buf_paddr);
}

void setup_page_write(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_PAGE_READ);
	rmem_set_src_addr(iomem, buf_paddr);

	for (int i = 0; i < pgwords; i++)
		buf[i] = i;
}

void setup_word_write(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_WORD_WRITE);
	rmem_set_src_addr(iomem, buf_paddr);

	buf[0] = memblade_make_exthead(16, 3);
	buf[1] = 0;
}

void setup_word_read(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_WORD_READ);
	rmem_set_src_addr(iomem, buf_paddr);
	rmem_set_dst_addr(iomem, buf_paddr + 8);

	buf[0] = memblade_make_exthead(16, 3);
}

void setup_atomic_add(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_ATOMIC_ADD);
	rmem_set_src_addr(iomem, buf_paddr);
	rmem_set_dst_addr(iomem, buf_paddr + 16);

	buf[0] = memblade_make_exthead(16, 3);
	buf[1] = 1;
}

void setup_comp_swap(void *iomem, uint64_t *buf, long buf_paddr)
{
	rmem_set_opcode(iomem, MB_OC_COMP_SWAP);
	rmem_set_src_addr(iomem, buf_paddr);
	rmem_set_dst_addr(iomem, buf_paddr + 24);

	buf[0] = memblade_make_exthead(16, 3);
	buf[1] = 4;
	buf[2] = 0;
}

int main(int argc, char *argv[])
{
	unsigned long dstmac = 0x0;
	int nprocs = 1, ntrials = 3, nstages = 1, increment = 1;
	int opt, fd;
	uint64_t *buf;
	long buf_paddr, barrier_page = 0, start_page = 4, pageno;
	struct timespec start, end;
	void *iomem;
	long *stagens;

	while ((opt = getopt(argc, argv, "n:m:d:p:s:b:q")) != -1) {
		switch (opt) {
		case 'n':
			ntrials = atoi(optarg);
			break;
		case 'm':
			nstages = atoi(optarg);
			break;
		case 'd':
			dstmac = strtol(optarg, NULL, 16);
			break;
		case 'p':
			nprocs = atoi(optarg);
			break;
		case 's':
			start_page = atol(optarg);
			break;
		case 'b':
			barrier_page = atol(optarg);
			break;
		case 'q':
			increment = 0;
			break;
		}
	}

	fd = open("/dev/remote-mem", O_RDWR);
	if (fd < 0) {
		perror("open()");
		return EXIT_FAILURE;
	}

	iomem = mmap(NULL, 0x30, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
	if (iomem == MAP_FAILED) {
		perror("mmap() iomem");
		return EXIT_FAILURE;
	}

	rmem_set_dstmac(iomem, dstmac);

	pgsize = sysconf(_SC_PAGESIZE);
	pgwords = pgsize / sizeof(uint64_t);
	buf = mmap_alloc(pgsize);
	if (buf == MAP_FAILED) {
		perror("mmap() srcpage");
		return EXIT_FAILURE;
	}

	buf_paddr = get_pfn(fd, buf);
	if (buf_paddr < 0) {
		fprintf(stderr, "Failed to translate page %p\n", buf);
		exit(EXIT_FAILURE);
	}
	buf_paddr *= pgsize;

	memset(buf, 0, pgsize);

	stagens = malloc(sizeof(long) * nstages * 6);
	if (stagens == NULL) {
		perror("malloc() stagens\n");
		exit(EXIT_FAILURE);
	}

	if (nprocs > 1) {
		wait_barrier_init(
			iomem, buf, buf_paddr,
			buf + 2, buf_paddr + 16, barrier_page);
	}

	pageno = start_page;

	for (int i = 0; i < nstages; i++) {
		if (nprocs > 1) {
			barrier(iomem, nprocs, buf, buf_paddr,
				buf + 2, buf_paddr + 16, barrier_page);
		}

		// Page Read
		setup_page_read(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i] = timediff(&end, &start);

		// Page Write
		setup_page_write(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i + 1] = timediff(&end, &start);

		// Word Read
		setup_word_read(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i + 2] = timediff(&end, &start);

		// Word Write
		setup_word_write(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i + 3] = timediff(&end, &start);

		// Atomic Add
		setup_atomic_add(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i + 4] = timediff(&end, &start);

		// Compare and Swap
		setup_comp_swap(iomem, buf, buf_paddr);
		mb();

		clock_gettime(CLOCK_MONOTONIC, &start);
		for (int j = 0; j < ntrials; j++) {
			rmem_set_pageno(iomem, pageno);
			rmem_send_sync(iomem);
			if (increment) pageno++;
		}
		clock_gettime(CLOCK_MONOTONIC, &end);

		stagens[6 * i + 5] = timediff(&end, &start);
	}

	for (int i = 0; i < nstages; i++) {
		long pgread_lat    = stagens[6 * i];
		long pgwrite_lat   = stagens[6 * i + 1];
		long wordread_lat  = stagens[6 * i + 2];
		long wordwrite_lat = stagens[6 * i + 3];
		long atomadd_lat   = stagens[6 * i + 4];
		long compswap_lat  = stagens[6 * i + 5];

		printf("Stage %d page read latency = %ld\n", i, pgread_lat / ntrials);
		printf("Stage %d page write latency = %ld\n", i, pgwrite_lat / ntrials);
		printf("Stage %d word read latency = %ld\n", i, wordread_lat / ntrials);
		printf("Stage %d word write latency = %ld\n", i, wordwrite_lat / ntrials);
		printf("Stage %d atomic add latency = %ld\n", i, atomadd_lat / ntrials);
		printf("Stage %d compare + swap latency = %ld\n", i, compswap_lat / ntrials);
	}

	if (nprocs > 1) {
		barrier(iomem, nprocs,
			buf, buf_paddr, buf + 2, buf_paddr + 16,
			barrier_page);
	}

	return 0;
}
