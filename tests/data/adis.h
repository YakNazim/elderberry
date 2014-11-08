
typedef struct {
	int number;
} ADISMessage;

void MIML_SENDER adis_data_out(ADISMessage *);
void MIML_RECEIVER adis_raw_in(unsigned char *, unsigned int, unsigned char *);

