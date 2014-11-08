#ifndef LOGGER_H_
#define LOGGER_H_

#include "adis.h"
#include "rollcontrol.h"

void MIML_INIT logger_init(int argc, char * argv[]);
void MIML_FINAL logger_final(void);
void MIML_RECEIVER log_receive_adis(ADISMessage *);
void MIML_RECEIVER log_receive_rc(RollServoMessage *);
#endif
