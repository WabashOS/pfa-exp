#include <stdio.h>
#include <stdlib.h>

#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>

#include "memblade.h"
#include "util.h"

#define BUFFER_PAGES 16
#define min(a, b) (((a) < (b)) ? (a) : (b))

int main(int argc, char *argv[])
{
	FILE *f;
	int c, devfd, npages, idx = 0;
	int pgsize = sysconf(_SC_PAGESIZE);
	int bufsize = BUFFER_PAGES * pgsize;
	void *buffer, *iomem;
	unsigned long dstmac = 0x0;
	size_t fsize;
	int startpage = 0;
	long *paddrs;

	while ((c = getopt(argc, argv, "d:s:")) != -1) {
		switch (c) {
		case 'd':
			dstmac = strtol(optarg, NULL, 16);
			break;
		case 's':
			startpage = atoi(optarg);
			break;
		default:
			fprintf(stderr, "Unrecognized option %c\n", c);
			exit(EXIT_FAILURE);
		}
	}

	if (optind == argc) {
		fprintf(stderr, "Usage: %s [-s <start_page>] [-d <dstmac>] data.bin\n", argv[0]);
		exit(EXIT_FAILURE);
	}

	f = fopen(argv[optind], "r");
	if (f == NULL) {
		fprintf(stderr, "Could not open %s\n", argv[optind]);
		perror("fopen()");
		exit(EXIT_FAILURE);
	}

	if (fseek(f, 0, SEEK_END)) {
		perror("fseek()");
		exit(EXIT_FAILURE);
	}

	fsize = ftell(f);
	if (fsize < 0) {
		perror("ftell()");
		exit(EXIT_FAILURE);
	}

	rewind(f);

	npages = fsize / pgsize;

	printf("Uploading %d pages starting at %d\n", npages, startpage);

	buffer = mmap_alloc(bufsize);
	if (buffer == MAP_FAILED) {
		perror("mmap()");
		exit(EXIT_FAILURE);
	}

	paddrs = malloc(BUFFER_PAGES * sizeof(long));
	if (paddrs == NULL) {
		perror("malloc()");
		exit(EXIT_FAILURE);
	}

	devfd = open("/dev/remote-mem", O_RDWR);
	if (devfd < 0) {
		fprintf(stderr, "Could not open /dev/remote-mem\n");
		perror("open()");
		exit(EXIT_FAILURE);
	}

	iomem = mmap(NULL, pgsize, PROT_READ|PROT_WRITE, MAP_SHARED, devfd, 0);
	if (iomem == MAP_FAILED) {
		perror("mmap()");
		exit(EXIT_FAILURE);
	}

	translate_pages(devfd, paddrs, buffer, BUFFER_PAGES);

	rmem_set_dstmac(iomem, dstmac);
	rmem_set_opcode(iomem, MB_OC_PAGE_WRITE);

	while (idx < npages) {
		int pages_to_read = min(npages - idx, BUFFER_PAGES);
		int nread = fread(buffer, pgsize, pages_to_read, f);

		if (nread == 0) {
			fprintf(stderr, "Unexpected end of file at page %d\n", idx);
			exit(EXIT_FAILURE);
		}

		if (nread < 0) {
			perror("fread()");
			exit(EXIT_FAILURE);
		}

		while (rmem_nreq(iomem) < nread) {}

		for (int j = 0; j < nread; j++) {
			rmem_set_src_addr(iomem, paddrs[j]);
			rmem_set_pageno(iomem, startpage + idx + j);
			rmem_send_req(iomem);
		}

		while (rmem_nresp(iomem) < nread) {}

		for (int j = 0; j < nread; j++)
			rmem_get_resp(iomem);

		idx += nread;
	}

	printf("Upload complete\n");

	munmap(iomem, pgsize);
	munmap(buffer, pgsize);
	close(devfd);
	fclose(f);

	return 0;
}
