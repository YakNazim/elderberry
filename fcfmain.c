/*
 * auto generated fcf
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/poll.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <errno.h>
#include <unistd.h>

#include "testIMU.h"
#include "testLoggerDisk.h"
#include "testLoggerScreen.h"
#include "fcfutils.h"


typedef void (*pollfd_callback)(int fd_idx);

struct fcffd {
	const char *token;
	pollfd_callback callback;
};

static struct pollfd *fds;
static struct fcffd *fds2;
static int nfds = 0;

static char buffer [1024];

void fcf_init() {
	// Calls all init functions
	init_theo_imu();
	init_diskLogger();

	// Fetch all FileDescriptors
	fcf_get_fd_structure(&fds, &fds2, &nfds);
}

void fcf_callback_gyr(int idx) {
	// generated function that is called when a file descriptor
	// that testIMU maps to MessageA is responsive.
	int rc = fileA_handler(fds[idx].fd, buffer, sizeof(buffer));

	if (rc > 0) {
		int len = rc;
		screenLogger_getMessage("gyr", buffer, len);
		diskLogger_getMessage("gyr", buffer, len);
	}
}


void fcf_callback_acc(int idx) {
	// generated function that is called when a file descriptor
	// that testIMU maps to MessageA is responsive.
	int rc = fileB_handler(fds[idx].fd, buffer, sizeof(buffer));

	if (rc > 0) {
		int len = rc;
		screenLogger_getMessage("acc", buffer, len);
		diskLogger_getMessage("acc", buffer, len);
	}
}

void fcf_callback_mouse(int idx){
	//mouse_callback(idx);
}


pollfd_callback fcf_get_callback_function(const char * token){
	printf("Token %s hoping to get callback function.\n", token);
	if(strcmp(token, "mouse") == 0){
		return fcf_callback_mouse;
	}
	else if(strcmp(token, "gyr") == 0){
		return fcf_callback_gyr;
	}
	else if(strcmp(token, "acc") == 0){
		return fcf_callback_acc;
	}

	printf("Uh-oh, we don't have a callback function for you. Back to the MIML file!\n");

	return NULL;
}



int fcf_main_loop_run() {

	int rc;
	int timeout = 5 * 1000;	// in ms

	for (;;)
	{
		/**
		*	Call poll() and wait for it to complete.
		*/
		printf("Waiting on poll()...\n");
		rc = poll(fds, nfds, timeout);

		/**
		*	Check to see if the poll call failed. 
		*/
		if (rc < 0){
			perror("  poll() failed");
			break;
		}

		/**
		*	poll timed out 
		*/
		if (rc == 0){
			//do something useful, e.g. call into libusb so that libusb can deal with timeouts
			printf("  poll() timed out.\n");
		}


		/**
		*	One or more descriptors are readable.  Need to 
		*	determine which ones they are. 
		*/
		int current_size = nfds;
		for (int i = 0; i < current_size; i++){
			/*********************************************************/
			/* Loop through to find the descriptors that returned    */
			/* POLLIN and determine whether it's the listening       */
			/* or the active connection.                             */
			/*********************************************************/
			if(fds[i].revents == 0) {
				continue;
			}

			/*********************************************************/
			/* If revents is not POLLIN, it's an unexpected result,  */
			/* log and end the server.                               */
			/*********************************************************/
//			if(fds[i].revents != POLLIN)
//			{
//				printf("  Error! revents = %d\n", fds[i].revents);
//
//			}

			printf("  Descriptor %d is readable\n", fds[i].fd);

			fds2[i].callback(i);
		}
	}

	return 0;
}
