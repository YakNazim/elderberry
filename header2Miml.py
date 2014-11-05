#!/usr/bin/env python

#     Assumptions:
#         - variable names not defined are replaced by ARG# variable name

import sys
import argparse
from elderberry.mimlgen import HeaderParse, WriteMiml

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('header', help='C header to convert to a MIML module')
    argparser.add_argument('cpp', help='Flags to pass to the C preprocessor')
    args = argparser.parse_args()

    if not args.header.endswith('.h'):
        print("Error: Input file not a .h file.")
        sys.exit(-1)
    basename = os.path.basename(args.header)[:-2]  # strip .h, leading path

    miml = HeaderParse(args.header, args.cpp)

    WriteMiml(miml.funcs, basename).dump()

