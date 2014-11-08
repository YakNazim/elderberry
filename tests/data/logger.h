#include "adis.h"
#include "rollcontrol.h"

void MIML_FINAL logger_final(void);
void MIML_INIT logger_init(void);
void MIML_RECEIVER log_receive_adis(ADISMessage *);
void MIML_RECEIVER log_receive_rc(RollServoMessage *);
