#ifndef ADIS_H_
#define ADIS_H_
typedef struct {
	int number;
} ADISMessage;

void MIML_SENDER adis_out(ADISMessage *);
void MIML_RECEIVER adis_raw(unsigned char *, unsigned int, unsigned char *);
#endif
