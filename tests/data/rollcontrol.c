#include "rollcontrol.h"


void rollcontrol_init(int argc, char * argv[]){

}

void rc_raw(unsigned char * buff, unsigned int len, unsigned char * time){

}
void rc_adis(ADISMessage * m){
	RollServoMessage n;
	n.number = m->number;
	rc_out(&n);
}

