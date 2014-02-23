#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ev.h>

static void stop_cb(struct ev_loop *loop, ev_signal *w, int revents){
    printf("Quitting \n");
    ev_break(loop, EVBREAK_ALL);
}

int main(int argc, char *argv[]){
    //todo: boilerplate
    //todo: ev_version check, ev_backends check

    int retval = EXIT_SUCCESS;

    struct ev_loop * loop;
    loop = ev_default_loop(0);
    if(!loop){
        fprintf(stderr, "Fatal: could not initialize libev\n");
        return EXIT_FAILURE;
    }

    ev_signal stop;
    ev_signal_init(&stop, stop_cb, SIGINT);
    ev_signal_start(loop, &stop);
    //todo: argc, argv passed to initialize. Use argp?
    if(modules_initialize(loop)){
        fprintf(stderr, "Fatal: module initialization failure\n");
        retval = EXIT_FAILURE;
    }else{
        ev_run (loop, 0);
    }
    modules_finalize(loop);

    return retval;
}
