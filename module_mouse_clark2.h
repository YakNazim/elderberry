/*
 * module_mouse_clark2.h
 *
 */

#ifndef MODULE_MOUSE_CLARK2_H_
#define MODULE_MOUSE_CLARK2_H_

void init_mouse_clark2 (void);
void finalize_mouse_clark2 (void);
extern void sendMessage_mouse_clark2(unsigned char *buffer, int length);

#endif /* MODULE_MOUSE_CLARK2_H_ */
