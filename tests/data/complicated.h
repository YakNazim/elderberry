#ifndef COMPLICATED_H_
#define COMPLICATED_H_

void normalFunc(void);
void inline funcWithNonAttrFuncspec(void);
void __attribute__((noreturn)) funcWithAttr(void);
void __attribute__((nonnull(1))) funcWithFuncAttr(void *);

void MIML_SENDER funcWithCollidingArgNames(int _arg1, int s, int _arg5);

#endif
