DOXYFILE := ./Doxyfile

LDLIBS = -lev
all: evutils

html:
	rm -rf ./html
	doxygen $(DOXYFILE)

pdf:
	(grep -v GENERATE_LATEX $(DOXYFILE) ; echo GENERATE_LATEX = YES) | doxygen -
	cd ./latex && $(MAKE) pdf
	mv ./latex/refman.pdf .
	rm -rf ./latex

distclean: clean
	rm -rf refman.pdf #./html 


clean:
	rm -f *.o *.d fc core
	rm -f $(MIMLMK) fcfmain.c fcfmain.h

.PHONY: html
