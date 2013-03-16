/**
 * @file fcfutils.h
 * @brief Utility functions for the flight control framework (fcf)
 * @details The core framework file, it starts in the main function, introducing the rogram.  This program has signal handlers for when the user exits abrubtly using ctrl+Z, allowing a graceful shutdown of the software.  The main function also initializes the framework and the modules before running the main loop. Lastly, this file contains the struct that holds the callback functions and source tokens of each device.  

<<<<<<<<<<<<<<<<<<<< LICENSING INFORMATION >>>>>>>>>>>>>>>>>>>>
\n FLIGHT CONTROL FRAMEWORK V0.1  Copyright (C) 2013\n
Ron Astin, Clark Wachsmuth, Chris Glasser, Josef Mihalits, Jordan Hewitt, Michael Hooper]\n\n
----------------------------------------------------------------\n
This program comes with ABSOLUTELY NO WARRANTY;\n for details please
visit http://www.gnu.org/licenses/gpl.html.\n\n
This is free software, and you are welcome to redistribute it\n
under certain conditions; For details, please visit\n
http://www.gnu.org/licenses/gpl.html.\n
----------------------------------------------------------------\n\n\n

                                           
 * @author Team Elderberry
 * @date March 2nd, 2013
 */
#ifndef _FCFUTILS_
#define _FCFUTILS_

#define TRUE             1
#define FALSE            0

#include <poll.h>

typedef void (*pollfd_callback)(struct pollfd *);
/**
 * @brief adds file descriptor on tot he end of the array
 * @details Checks to see if the file descriptor arrays are full.  If the arrays are full it calls the expand_arrays() fucntion (this will double the size of the arrays). It adds information to two arrays, the fds and fdx arrays.  The fds array has pollfd pointers (required by the poll system call) and the fdx array has fcffd pointers (required by our framework [containing callback functions and other information])
 * @param fd -   
 * @param events - 
 * @param cb - 
 * @return index value of newest file descriptor
 */
extern int fcf_add_fd(int fd, short events, pollfd_callback cb);
/**
 * @brief simply removes a specified file descriptor from the arrays
 * @details If there are no fds in the array, the function errors out. If there are fd's in the arrays they are removed from both the fds and fdx arrays.
 * @param fd -   
 */
extern void fcf_remove_fd(int fd);

/**
 * @brief returns the fds array info
 * @details Specifically this function returns the pollfd* information from the fds array for the specified index value
 * @param idx - index value
 * @return pollfd* info for specified index value
 */
extern struct pollfd * fcf_get_fd(int idx);
/**
 * @brief stops main loop by setting run_fc to 0
 */
extern void fcf_stop_main_loop(void);

/**
 * @brief Main function for framework
 * @details Prints the licensing information, and software version number.  It contains the signal handler for graceful shutdown should the user CTRL-C out of the program. It then initializes the framework and runns the polling loop.
 * @return EXIT_SUCCESS
 * @return EXIT_FAILURE
 */
int main(int argc, char *argv[]);

#endif