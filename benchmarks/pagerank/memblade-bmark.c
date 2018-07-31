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
int write_max_inflight = 16, read_max_inflight = 16, inflight = 0;
long npages = 64, start_page = 4;
int increment = 1;

void send_page_writes(void *iomem, unsigned long *srcframes, int *nsent)
{
	int nreq = rmem_nreq(iomem);

	while (nreq > 0 && *nsent < npages && inflight < write_max_inflight) {
		rmem_set_src_addr(iomem, srcframes[*nsent]);
		if (increment) {
			rmem_set_pageno(iomem, start_page + *nsent);
		} else {
			rmem_set_pageno(iomem, start_page);
		}
		rmem_send_req(iomem);
		(*nsent)++;
		inflight++;
		nreq--;
	}
}

void complete_requests(void *iomem, int *nrecv)
{
	int nresp = rmem_nresp(iomem);

	while (nresp > 0 && *nrecv < npages) {
		rmem_get_resp(iomem);
		(*nrecv)++;
		inflight--;
		nresp--;
	}
}

void benchmark_writes(void *iomem, unsigned long *srcframes)
{
	int nsent = 0, nrecv = 0;

	rmem_set_opcode(iomem, MB_OC_PAGE_WRITE);

	while (nsent < npages) {
		send_page_writes(iomem, srcframes, &nsent);
		complete_requests(iomem, &nrecv);
	}

	while (nrecv < npages) {
		complete_requests(iomem, &nrecv);
	}
}

void send_page_reads(void *iomem, unsigned long *dstframes, int *nsent)
{
	int nreq = rmem_nreq(iomem);

	while (nreq > 0 && *nsent < npages && inflight < read_max_inflight) {
		rmem_set_dst_addr(iomem, dstframes[*nsent]);
		if (increment) {
			rmem_set_pageno(iomem, start_page + *nsent);
		} else {
			rmem_set_pageno(iomem, start_page);
		}
		rmem_send_req(iomem);
		(*nsent)++;
		inflight++;
		nreq--;
	}
}

void benchmark_reads(void *iomem, unsigned long *dstframes)
{
	int nsent = 0, nrecv = 0;

	rmem_set_opcode(iomem, MB_OC_PAGE_READ);

	while (nsent < npages) {
		send_page_reads(iomem, dstframes, &nsent);
		complete_requests(iomem, &nrecv);
	}

	while (nrecv < npages) {
		complete_requests(iomem, &nrecv);
	}
}

static int check_page(uint64_t *src, uint64_t *dst)
{
	for (int i = 0; i < pgwords; i++) {
		if (dst[i] != src[i]) {
			fprintf(stderr, "Error @ %d: %lx != %lx\n",
					i, dst[i], src[i]);
			return -1;
		}
	}

	return 0;
}

int main(int argc, char *argv[])
{
	void *iomem;
	uint64_t *src, *dst;
	int fd, opt, ret = 0;
	unsigned long *srcframes, *dstframes, dstmac = 0;
	struct timespec start, end;
	int nprocs = 1, binit = 0;
	long barrier_page = 0;

	while ((opt = getopt(argc, argv, "n:d:s:w:r:p:b:iq")) != -1) {
		switch (opt) {
		case 'n':
			npages = atol(optarg);
			break;
		case 'd':
			dstmac = strtol(optarg, NULL, 16);
			break;
		case 's':
			start_page = atol(optarg);
			break;
		case 'w':
			write_max_inflight = atoi(optarg);
			break;
		case 'r':
			read_max_inflight = atoi(optarg);
			break;
		case 'p':
			nprocs = atoi(optarg);
			break;
		case 'b':
			barrier_page = atol(optarg);
			break;
		case 'i':
			binit = 1;
			break;
		case 'q':
			increment = 0;
			break;
		default:
			fprintf(stderr, "Unrecognized flag %c\n", opt);
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

	src = mmap_alloc(pgsize * npages);
	if (src == MAP_FAILED) {
		perror("mmap() srcpage");
		return EXIT_FAILURE;
	}

	dst = mmap_alloc(pgsize * npages);
	if (dst == MAP_FAILED) {
		perror("mmap() dstpage");
		return EXIT_FAILURE;
	}

	for (int i = 0; i < pgwords * npages; i++) {
		unsigned long half = i;
		src[i] = (half << 32) | half;
		dst[i] = 0;
	}

	srcframes = malloc(sizeof(long) * npages);
	if (srcframes == NULL) {
		perror("malloc()");
		exit(EXIT_FAILURE);
	}

	dstframes = malloc(sizeof(long) * npages);
	if (dstframes == NULL) {
		perror("malloc()");
		exit(EXIT_FAILURE);
	}

	translate_pages(fd, srcframes, src, npages);
	translate_pages(fd, dstframes, dst, npages);

	printf("Benchmark npages=%ld, start_page=%ld\n", npages, start_page);

	if (nprocs > 1) {
		if (binit)
			init_barrier(iomem, src, srcframes[0], barrier_page);
		else
			wait_barrier_init(
				iomem, src, srcframes[0],
				dst, dstframes[0],
				barrier_page);
	}

	printf("Write benchmark: %d requests inflight\n", write_max_inflight);

	if (nprocs > 1)
		barrier(iomem, nprocs, src, srcframes[0], dst, dstframes[0], barrier_page);

	clock_gettime(CLOCK_MONOTONIC, &start);
	benchmark_writes(iomem, srcframes);
	clock_gettime(CLOCK_MONOTONIC, &end);

	printf("Write Gbps: %ld\n", (8 * pgsize * npages) / timediff(&end, &start));

	printf("Read benchmark: %d requests inflight\n", read_max_inflight);

	if (nprocs > 1)
		barrier(iomem, nprocs, src, srcframes[0], dst, dstframes[0], barrier_page);

	clock_gettime(CLOCK_MONOTONIC, &start);
	benchmark_reads(iomem, dstframes);
	clock_gettime(CLOCK_MONOTONIC, &end);

	printf("Read Gbps: %ld\n",  (8 * pgsize * npages) / timediff(&end, &start));

	for (int i = 0; i < npages; i++) {
		void *srcpage = (increment) ?
			(src + i * pgwords) : (src + (npages - 1) * pgwords);
		void *dstpage = dst + (i * pgwords);

		if (check_page(srcpage, dstpage)) {
			fprintf(stderr, "Page %d\n", i);
			ret = EXIT_FAILURE;
		}
	}

	if (nprocs > 1) {
		if (binit)
			destroy_barrier(iomem, src, srcframes[0], barrier_page);
		barrier(iomem, nprocs, src, srcframes[0], dst, dstframes[0], barrier_page);
	}

	return ret;
}
