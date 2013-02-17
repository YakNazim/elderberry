/*
 * A stripped down version of the PSAS av3-fc code found here:
 * http://git.psas.pdx.edu/av3-fc.git
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <errno.h>
#include <unistd.h>

#include "fc.h"
#include "libusb-basic.h"
#include "logging.h"
#include "miml.h"




static void signalhandler(int signum) {
    printf ("\n **signal handler: signum = %d", signum);

    if (signum == SIGINT)  {
        stop_main_loop ();
    }
}

void handleErrorPoll(void) {
    int err = errno;
    char *msg = strerror(err);
    printf ("\n poll error handling: errno=%d %s ", err, msg);
    switch(err) {
        case EFAULT: printf ("EFAULT"); break;
        case EINTR: printf ("EINTR"); break;
        case EINVAL: printf ("EINVAL"); break;
        case ENOMEM: printf ("ENOMEM"); break;
    }
    printf_tagged_message(FOURCC('L', 'O', 'G', 'S'), "\n poll returned with errno=%d %s", err, msg);
}


int main(int argc, char **argv)
{
    int opt;
    while ( (opt = getopt (argc, argv, "g:")) != -1) {
        switch (opt) {
        case -1:
            break;
        case 'g':
            set_gps_devicepath (optarg);
            break;
        case 't':
            break;
        default: /* '?' */
            fprintf(stderr, "Usage: %s [-g Device path]\n",
                    argv[0]);
            exit(EXIT_FAILURE);
        }
    }

    signal (SIGUSR1, signalhandler);
    signal (SIGUSR2, signalhandler);
    signal (SIGINT, signalhandler);

    init_logging();

    libusbSource * usb_source = libusbSource_new();
    if(usb_source == NULL){
        exit(1);
    }

    FCF_Init(usb_source);
    //comment out the devices you don't have or want
    init_gps(usb_source);
    init_mouse(usb_source);     //read from usb mouse; set your hw values in is_mouse()
    init_mouse2(usb_source);    //read from a 2nd usb mouse; set your hw values in is_mouse2()
    init_virtgyro(usb_source);  //read from socket

    run_main_loop(usb_source);

    printf("\n");
    return 0;
}
