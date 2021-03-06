#ifndef __UTIL_H__
#define __UTIL_H__

#include <time.h>
#include <sys/mman.h>

static inline long timediff(struct timespec *a, struct timespec *b)
{
	return (a->tv_sec - b->tv_sec) * 1e9 + (a->tv_nsec - b->tv_nsec);
}

static inline void mb(void) {
#ifdef __amd64__
  asm volatile ("mfence" ::: "memory");
#else
#ifndef HOST_DEBUG
	asm volatile ("fence");
#endif
#endif
}

#endif
