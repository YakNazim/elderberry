/* DO NOT EDIT THIS FILE
 * It is auto-generated by codeGen.py
 * from the Elderberry framework.
 */

#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ev.h>
#include <ucontext.h>

//headers


static ucontext_t ripctx;
static ucontext_t startctx;
static bool ripping = false;

static void unrip(struct pollfd * pfd){
	removefd();
	ripping = false;
	setcontext(&ripctx);
}

void stackRip(int fd, short events) {
	getcontext(&ripctx);
	if(!ripping){
		return;
	}
	ripping = true;
	addfd();
	setcontext(&startctx);
}

static void modules_initialize(int argc, char *argv[]){
//initfinal
}

//wiring

static void stop_cb(struct ev_loop *loop, ev_signal *w, int revents){
	ev_break(loop, EVBREAK_ALL);
}

int main(int argc, char *argv[]){

	int major = ev_version_major();
	int minor = ev_version_minor();
	if(!(major == EV_VERSION_MAJOR && minor >= EV_VERSION_MINOR)){
		errx(EXIT_FAILURE,
		     "Fatal: libev version mismatch. Expected %d.%d but got %d.%d",
		     EV_VERSION_MAJOR, EV_VERSION_MINOR, major, minor);
	}
	if(!ev_recommended_backends()){
		errx(EXIT_FAILURE, "Fatal: libev recommended backend not available");
	}

	if(!EV_DEFAULT){
		errx(EXIT_FAILURE, "Fatal: could not initialize libev loop");
	}

	ev_signal stop;
	ev_signal_init(&stop, stop_cb, SIGINT);
	ev_signal_start(EV_DEFAULT_UC_ &stop);
	modules_initialize(argc, argv);
	ev_run(EV_DEFAULT_UC_ 0);

	return EXIT_SUCCESS;
}
