
#include "adis.h"


void adis_raw_in(unsigned char * buff, unsigned int len, unsigned char * time){
	ADISMessage m = {len};
	adis_data_out(m);
}

