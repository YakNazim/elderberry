#include "rollcontrol.h"


void rollcontrol_init(int argc, char * argv[]){

}

void rc_raw_ld_in(unsigned char * buff, unsigned int len, unsigned char * time){

}
void rc_receive_imu(ADISMessage * m){
	RollServoMessage n;
	n.number = m.number;
	rc_send_servo(&n);
}

