#ifndef ROLLCONTROL_H_
#define ROLLCONTROL_H_

#include "adis.h"

typedef struct {
	int number;
} RollServoMessage;

void MIML_INIT rollcontrol_init(void);
void MIML_RECEIVER rc_raw_ld_in(unsigned char *, unsigned int, unsigned char *);
void MIML_RECEIVER rc_receive_imu(ADISMessage *);
void MIML_SENDER rc_send_servo(RollServoMessage *);
#endif
