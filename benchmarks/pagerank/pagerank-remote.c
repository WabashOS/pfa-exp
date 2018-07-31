#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "memblade.h"
#include "pagerank.h"
#include "util.h"
#include "barrier.h"

#define BLOCK_SIZE 128
#define MAX_ITERS 30

//#define INSTRUMENT_COARSE
//#define INSTRUMENT_FINE

int pgsize, pgdoubles;
int nprocs = 1, procid = 0;
long barrier_page = 0;

struct page_buffer {
	void *data;
	uintptr_t paddr;
};

void alloc_buffers(int fd, struct page_buffer *buffers, int n)
{
	for (int i = 0; i < n; i++) {
		long pfn;

		buffers[i].data = mmap(
			NULL, pgsize, PROT_READ|PROT_WRITE,
			MAP_SHARED|MAP_ANONYMOUS, -1, 0);
		if (buffers[i].data == NULL) {
			fprintf(stderr, "Could not allocate buffer\n");
			exit(EXIT_FAILURE);
		}

		pfn = get_pfn(fd, buffers[i].data);
		if (pfn < 0) {
			fprintf(stderr, "Failed to translate %p\n", buffers[i].data);
			exit(EXIT_FAILURE);
		}
		buffers[i].paddr = pfn * pgsize;
	}
}

void free_buffers(struct page_buffer *buffers, int n)
{
	for (int i = 0; i < n; i++)
		munmap(buffers[i].data, pgsize);
}

void read_sync(int fd, void *iomem, double *dst, long pageno, int n)
{
	for (int i = 0; i < n; i += pgdoubles) {
		unsigned long pfn;

		pfn = get_pfn(fd, dst + i);
		if (pfn < 0) {
			fprintf(stderr, "Could not translate %p\n", dst + i);
			exit(EXIT_FAILURE);
		}

		rmem_wait_req(iomem, 1);
		rmem_read_issue(iomem, pfn * pgsize, pageno);

		rmem_wait_resp(iomem, 1);
		rmem_get_resp(iomem);

		pageno++;
	}
}

void matmul_buffered(struct page_buffer *buffers,
		double *src_v, double *dst_v, int m, int n)
{
	for (int bj = 0; bj < m; bj += BLOCK_SIZE) {
		for (int i = 0; i < n; i+=4) {
			size_t offset = bj * sizeof(double);
			dotprod4(&dst_v[i],
				buffers[i].data   + offset,
				buffers[i+1].data + offset,
				buffers[i+2].data + offset,
				buffers[i+3].data + offset,
				&src_v[bj], BLOCK_SIZE);
		}
	}
}

void send_buffer_reads(
		void *iomem, struct page_buffer *buffers,
		long startpage, int pages_per_row)
{
	rmem_wait_req(iomem, MAX_INFLIGHT);

	for (int i = 0; i < MAX_INFLIGHT; i++) {
		long pageno = startpage + i * pages_per_row;
		rmem_read_issue(iomem, buffers[i].paddr, pageno);
	}
}

void matmul(
	void *iomem, struct page_buffer *buffers,
	long startpage, double *src_v, double *dst_v, int n)
{
	int pages_per_row = n / pgdoubles;
	int half = 0;
	int nrows = (n / nprocs);
	int startrow = nrows * procid;
	int endrow = startrow + nrows;
	long pstart = startpage + startrow * pages_per_row;
	long pageno = pstart;
#ifdef INSTRUMENT_FINE
	long comm_time = 0, compute_time = 0;
	struct timespec start, end;
#endif

#ifdef INSTRUMENT_FINE
	clock_gettime(CLOCK_MONOTONIC, &start);
#endif
	for (int i = startrow; i < endrow; i++)
		dst_v[i] = 0.0;
#ifdef INSTRUMENT_FINE
	clock_gettime(CLOCK_MONOTONIC, &end);
	compute_time += timediff(&end, &start);
#endif

#ifdef INSTRUMENT_FINE
	clock_gettime(CLOCK_MONOTONIC, &start);
#endif
	send_buffer_reads(iomem, buffers, pageno, pages_per_row);
#ifdef INSTRUMENT_FINE
	clock_gettime(CLOCK_MONOTONIC, &end);
	comm_time += timediff(&end, &start);
#endif

	for (int j = 0; j < pages_per_row; j++) {
		for (int i = startrow; i < endrow; i += MAX_INFLIGHT) {
			int nexthalf = !half;
			long next_pageno;

			pageno = startpage + i * pages_per_row + j;
			if ((i + MAX_INFLIGHT) == endrow)
				next_pageno = pstart + j + 1;
			else
				next_pageno = pageno + pages_per_row * MAX_INFLIGHT;

			// complete the rmem reads for this block
#ifdef INSTRUMENT_FINE
			clock_gettime(CLOCK_MONOTONIC, &start);
#endif
			rmem_complete(iomem, MAX_INFLIGHT);
#ifdef INSTRUMENT_FINE
			clock_gettime(CLOCK_MONOTONIC, &end);
			comm_time += timediff(&end, &start);
#endif

			// send the rmem reads for the next block
			if ((i + MAX_INFLIGHT) < endrow || j < (pages_per_row - 1)) {
#ifdef INSTRUMENT_FINE
				clock_gettime(CLOCK_MONOTONIC, &start);
#endif
				send_buffer_reads(
					iomem, &buffers[nexthalf * MAX_INFLIGHT], 
					next_pageno, pages_per_row);
#ifdef INSTRUMENT_FINE
				clock_gettime(CLOCK_MONOTONIC, &end);
				comm_time += timediff(&end, &start);
#endif
			}

#ifdef INSTRUMENT_FINE
			clock_gettime(CLOCK_MONOTONIC, &start);
#endif
			matmul_buffered(&buffers[half * MAX_INFLIGHT],
					&src_v[j * pgdoubles], &dst_v[i],
					pgdoubles, MAX_INFLIGHT);
#ifdef INSTRUMENT_FINE
			clock_gettime(CLOCK_MONOTONIC, &end);
			compute_time += timediff(&end, &start);
#endif

			half = nexthalf;
		}
	}

#ifdef INSTRUMENT_FINE
	printf("compute time: %ld\n", compute_time);
	printf("communication time: %ld\n", comm_time);
#endif
}

static inline void buf_barrier(void *iomem, struct page_buffer *buffer)
{
	barrier(iomem, nprocs,
			buffer->data, buffer->paddr,
			buffer->data + 16, buffer->paddr + 16,
			barrier_page);
}

int pagerank(
	void *iomem, struct page_buffer *buffers, long startpage,
	double *v, unsigned long *vpaddr, int n, double err)
{
	int iters = 0;
	long resultpage = startpage + n * (n + 1) / pgdoubles;
	double *last_v = v + n, *cur_v = v;
	unsigned long *last_vpaddr = vpaddr + n / pgdoubles;
	unsigned long *cur_vpaddr = vpaddr;
#ifdef INSTRUMENT_COARSE
	struct timespec start, end;
#endif

	do {
		double *temp_v = last_v;
		unsigned long *temp_vpaddr = last_vpaddr;
		last_v = cur_v; last_vpaddr = cur_vpaddr;
		cur_v = temp_v; cur_vpaddr = temp_vpaddr;
#ifdef INSTRUMENT_COARSE
		clock_gettime(CLOCK_MONOTONIC, &start);
#endif
		matmul(iomem, buffers, startpage, last_v, cur_v, n);
#ifdef INSTRUMENT_COARSE
		clock_gettime(CLOCK_MONOTONIC, &end);
		printf("matmul: %ld\n", timediff(&end, &start));
#endif
		if (nprocs > 1) {
#ifdef INSTRUMENT_COARSE
			clock_gettime(CLOCK_MONOTONIC, &start);
#endif
			buf_barrier(iomem, &buffers[0]);
#ifdef INSTRUMENT_COARSE
			clock_gettime(CLOCK_MONOTONIC, &end);
			printf("barrier: %ld\n", timediff(&end, &start));
			clock_gettime(CLOCK_MONOTONIC, &start);
#endif
			push_result(iomem, resultpage, cur_v, cur_vpaddr, n);
#ifdef INSTRUMENT_COARSE
			clock_gettime(CLOCK_MONOTONIC, &end);
			printf("push_result: %ld\n", timediff(&end, &start));
			clock_gettime(CLOCK_MONOTONIC, &end);
#endif
			buf_barrier(iomem, &buffers[0]);
#ifdef INSTRUMENT_COARSE
			clock_gettime(CLOCK_MONOTONIC, &end);
			printf("barrier: %ld\n", timediff(&end, &start));
			clock_gettime(CLOCK_MONOTONIC, &end);
#endif
			pull_result(iomem, resultpage, cur_v, cur_vpaddr, n);
#ifdef INSTRUMENT_COARSE
			clock_gettime(CLOCK_MONOTONIC, &end);
			printf("pull_result: %ld\n", timediff(&end, &start));
#endif
		}
		//printf("iter: %d\n", iters);
		//print_vec(cur_v, n);
		//printf("sum: %f\n", sum_vec(cur_v, n));
		iters += 1;
	} while (!converged(cur_v, last_v, n, err) && iters < MAX_ITERS);

	return iters;
}

void print_matrix(void *iomem, struct page_buffer *buffers, long startpage, int n)
{
	long pageno = startpage;
	int npages = (n * n) / pgdoubles;

	while (npages > 0) {
		rmem_read_issue(iomem, buffers[0].paddr, pageno);
		rmem_complete(iomem, 1);
		print_vec(buffers[0].data, pgdoubles);
		pageno++;
		npages--;
	}
}

int main(int argc, char *argv[])
{
	struct timespec start, end;
	double *ranks, *expected, *result, err = 1e-8;
	long nanos, startpage = 0;
	int iters, fd, c, n = 0;
	struct page_buffer buffers[2 * MAX_INFLIGHT];
	long dstmac = 0x0;
	unsigned long *rankpaddr;
	void *iomem;

	pgsize = sysconf(_SC_PAGESIZE);
	pgdoubles = pgsize / sizeof(double);

	while ((c = getopt(argc, argv, "n:d:s:e:p:i:")) != -1) {
		switch (c) {
		case 'n':
			n = atoi(optarg);
			break;
		case 'd':
			dstmac = strtol(optarg, NULL, 16);
			break;
		case 's':
			startpage = atol(optarg);
			break;
		case 'e':
			err = atof(optarg);
			break;
		case 'p':
			nprocs = atoi(optarg);
			break;
		case 'i':
			procid = atoi(optarg);
			break;
		default:
			fprintf(stderr, "Unrecognized option %c\n", c);
			exit(EXIT_FAILURE);
		}
	}

	if (n < pgdoubles) {
		printf("Matrix dimension N=%d too small\n", n);
		exit(EXIT_FAILURE);
	}

	ranks = mmap_alloc(2 * n * sizeof(double));
	if (ranks == MAP_FAILED) {
		perror("mmap() ranks");
		exit(EXIT_FAILURE);
	}

	expected = mmap_alloc(n * sizeof(double));
	if (expected == MAP_FAILED) {
		perror("mmap() expected");
		exit(EXIT_FAILURE);
	}

	for (int i = 0; i < 2 * n; i++)
		ranks[i] = 1.0 / n;

	fd = open("/dev/remote-mem", O_RDWR);
	if (fd < 0) {
		perror("open()");
		exit(EXIT_FAILURE);
	}

	iomem = mmap(NULL, pgsize, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
	if (iomem == MAP_FAILED) {
		perror("mmap()");
		exit(EXIT_FAILURE);
	}

	rmem_set_dstmac(iomem, dstmac);

	alloc_buffers(fd, buffers, 2 * MAX_INFLIGHT);

	barrier_page = startpage + n * (n + 2) / pgdoubles;
	if (nprocs > 1) {
		if (procid == 0)
			init_barrier(
				iomem, buffers[0].data, buffers[0].paddr,
				barrier_page);
		else
			wait_barrier_init(iomem,
				buffers[0].data, buffers[0].paddr,
				buffers[0].data + 16, buffers[0].paddr + 16,
				barrier_page);
	}

	rankpaddr = malloc(sizeof(unsigned long) * 2 * n / pgdoubles);
	if (rankpaddr == NULL) {
		perror("malloc() rankpaddr");
		exit(EXIT_FAILURE);
	}
	translate_pages(fd, rankpaddr, ranks, 2 * n / pgdoubles);

	read_sync(fd, iomem, expected, startpage + (n * n) / pgdoubles, n);

	//print_matrix(iomem, buffers, startpage, n);

	if (nprocs > 1) buf_barrier(iomem, &buffers[0]); else mb();
	clock_gettime(CLOCK_MONOTONIC, &start);
	iters = pagerank(iomem, buffers, startpage, ranks, rankpaddr, n, err);
	if (nprocs > 1) buf_barrier(iomem, &buffers[0]); else mb();
	clock_gettime(CLOCK_MONOTONIC, &end);
	nanos = timediff(&end, &start);

	result = ((iters % 2) == 0) ? ranks : ranks + n;

	if (!converged(result, expected, n, err)) {
		fprintf(stderr, "PageRank result does not match expected\n");
		exit(EXIT_FAILURE);
	}

	printf("N = %d\n", n);
	printf("iterations = %d\n", iters);
	printf("nanos = %ld\n", nanos);

	if (nprocs > 1) {
		if (procid == 0)
			destroy_barrier(
				iomem, buffers[0].data, buffers[0].paddr,
				barrier_page);
		buf_barrier(iomem, &buffers[0]);
	}

	free_buffers(buffers, 2 * MAX_INFLIGHT);
	munmap(ranks, 2 * n * sizeof(double));
	munmap(expected, n * sizeof(double));
	munmap(iomem, pgsize);
	free(rankpaddr);
	close(fd);

	return 0;
}
