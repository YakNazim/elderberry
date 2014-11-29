#ifndef COMPLICATED_H_
#define COMPLICATED_H_

void normalFunc(void);
void __attribute__((noreturn)) funcWithAttr(void);
void __attribute__((nonnull(1))) funcWithFuncAttr(void *);

void MIML_SENDER funcWithCollidingArgNames(int _arg1, int _arg2, int _arg3);

#endif
