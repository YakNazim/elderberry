#include <stdio.h>
#include <stdlib.h>
#include <poll.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <string.h>
#include "fcfutils.h"
#include "fcfmain.h"


struct fcffd {
	const char *token;
	pollfd_callback callback;
};

static const int MAXFD = 100;
static struct pollfd fds[MAXFD];
static struct fcffd fds2[MAXFD];
static int nfds = 0;

// Add file descriptor to array of FDs.
extern void fcf_add_fd(const char *token, int fd) {
	fds[nfds].fd = fd;
	fds[nfds].events = POLLIN | POLLPRI;
	fds2[nfds].token = token;
	fds2[nfds].callback = fcf_get_callback_function(token);
	nfds++;
}


int fcf_remove_all_fd(const char *fd_src) {
  // Remove all file descriptors that were added under given source token.

	// If there are no fds, return 0 -- or error code.
	if(nfds <= 0)
		return 0;

	int i = 0, removed = 0;
	
	for(i=0; i<nfds; i++){
		// NOTE: if non-null-terminated strings, use strncmp with length
		if(strcmp(fds2[i].token, fd_src) == 0){

			// If matching fd is last in array.
			if(nfds - 1 == i){
				nfds--;
				removed++;
				return removed;
			}
			
			// Replace fd at index i with last fd in array.
			memmove(&fds[i], &fds[nfds - 1], sizeof(struct pollfd));

			// Replace fcffd at index i with last fcffd in array.
			memmove(&fds2[i], &fds2[nfds - 1], sizeof(struct fcffd));
			
			// Decrement number of fds and increment amount removed.
			nfds--;
			removed++;
		}
	}

	return removed;
}


void fcf_get_fd_structure(struct pollfd **_fds, struct fcffd **_fds2, int *_nfds) {
	*_fds = fds;
	*_fds2 = fds2;
	*_nfds = nfds;
}


