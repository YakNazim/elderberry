#ifndef _FCFMAIN_
#define _FCFMAIN_

#define TRUE             1
#define FALSE            0

typedef void (*pollfd_callback)(int fd_idx);
extern pollfd_callback fcf_get_callback_function(const char *);

#endif
