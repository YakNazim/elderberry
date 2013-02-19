/**
 *  @file testLoggerScreen.c
 *  @brief logs all info into a terminal session.
 *  @details Simple piece of code that passes data to be written to the active terminal session.
 *  @author Clark Wachsmuth
 *  @date February 8th, 2013
 */

#include <stdio.h>


void init_screenLogger () {
	
}

// src... name of source
// buffer... message
// len... length of data in buffer

void screenLogger_getMessage(const char *src, char *buffer, int len) {
	// some data has been passed into this function for consumption.
	
	printf("%s sends: \n", src);
	for (int i = 0; i < len; i++) {
		char c = buffer[i];
		printf ("%X(%c) ", c, c < 32 ? '.': c);
	}
	printf("\n");
}

void screenLogger_getMouseMessage(const char *src, unsigned char *buffer, int len){
	char but = buffer[0];
	
	switch((int)but){
		case 1:
			printf("Mouse button(s): [X][0][0]\n");
			break;
		case 2:
			printf("Mouse button(s): [0][0][X]\n");
			break;
		case 3:
			printf("Mouse button(s): [X][0][X]\n");
			break;
		case 4:
			printf("Mouse button(s): [0][X][0]\n");
			break;
		case 5:
			printf("Mouse button(s): [X][X][0]\n");
			break;
		case 6:
			printf("Mouse button(s): [0][X][X]\n");
			break;
		case 7:
			printf("Mouse button(s): [X][X][X]\n");
			break;
		default: 
			printf("---------\n");
			break;
		
	}
}


// Other private functions to do stuff.
