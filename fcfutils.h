#ifndef _FCFUTILS_
#define _FCFUTILS_

#define TRUE             1
#define FALSE            0

extern void fcf_add_fd(const char*, int);
extern int fcf_remove_all_fd(const char*);
extern void fcf_get_fd_structure(struct pollfd **_fds, struct fcffd **_fds2, int *_nfds);
#endif
