#ifndef ROLLCONTROL_H_
#define ROLLCONTROL_H_

#include "adis.h"

typedef struct {
	int number;
} RollServoMessage;

void MIML_INIT rollcontrol_init(int argc, char * argv[]);
void MIML_RECEIVER rc_raw(unsigned char *, unsigned int, unsigned char *);
void MIML_RECEIVER rc_adis(ADISMessage *);
void MIML_SENDER rc_out(RollServoMessage *);
#endif
