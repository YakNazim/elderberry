#ifndef ETHMUX_H_
#define ETHMUX_H_

void MIML_INIT ethmux_init(int argc, char * argv[]);
void MIML_FINAL ethmux_final(void);
void MIML_SENDER demuxed_adis(unsigned char * buffer, unsigned int length, unsigned char * timestamp);
void MIML_SENDER demuxed_rc(unsigned char * buffer, unsigned int length, unsigned char * timestamp);

#endif
