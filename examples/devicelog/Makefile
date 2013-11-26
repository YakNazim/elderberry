OPTSLIVE := -flto -O3 
OPTSDEV  := -g
OPTSPROF := -O3 -pg
OPTS     := -ffast-math
WARNINGS := -Wall
CFLAGS   := -MD -std=gnu99 $(OPTS) $(WARNINGS) -fno-strict-aliasing $(shell pkg-config --cflags libusb-1.0)
LDLIBS   := -lrt $(shell pkg-config --libs libusb-1.0)
.DEFAULT_GOAL := all
DOXYFILE := ./Doxyfile
OBJECTS  += ../../fcfutils.o  fcfmain.o  ../../utils_sockets.o ../../utils_libusb-1.0.o

MAINMIML ?= Main.miml
MIMLMK   ?= miml.mk

-include $(MIMLMK)

all: CFLAGS += $(OPTSLIVE)

all: CFLAGS += $(OPTSLIVE)
all: fc

debug: CFLAGS  += $(OPTSDEV)
debug: LDFLAGS += $(OPTSDEV)
debug: fc

fc: $(OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LOADLIBES) $(LDLIBS)

miml: $(MIMLMK)

$(MIMLMK): $(MAINMIML)
	python ../../codeGen.py -mch $^


clean:
	rm -f *.o *.d fc core
	rm -f $(MIMLMK) fcfmain.c fcfmain.h
