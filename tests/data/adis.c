
#include "adis.h"


void adis_raw(unsigned char * buff, unsigned int len, unsigned char * time){
	ADISMessage m = {len};
	adis_out(&m);
}

