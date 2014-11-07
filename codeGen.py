#!/usr/bin/env python
#
# codeGen.py was written by Ron Astin (rastin71 - github)
# 03/16/13 PSU Senior Capstone project (Team Elderberry).
# Sponsor client: Portland State Aerospace Society (PSAS) http://psas.pdx.edu/
#
# Team Elderberry:
# 	Ron Astin
# 	Chris Glasser
# 	Jordan Hewitt
# 	Mike Hooper
# 	Josef Mihalits
# 	Clark Wachsmuth

import logging
import argparse
from elderberry.codegen import Parser

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', help='Generate C files', action='store_true')
    argparser.add_argument('-m', help='Generate Makefiles', action='store_true')
    argparser.add_argument('-v', help='Enable additional logging', action='count')
    argparser.add_argument('-g', help='Code generator config filename')
    argparser.add_argument('miml', help='Main miml filename')
    args = argparser.parse_args()

    level = logging.WARNING
    if args.v == 1:
        level = logging.INFO
    if args.v > 1:
        level = logging.DEBUG
    logging.basicConfig(format='%(levelname)s: %(message)s', level=level)

    modeflags = {}
    modeflags['code'] = args.c
    modeflags['make'] = args.m

    config = args.g if args.g else 'cg.conf'

    parser = Parser(config, modeflags)
    parser.parse(args.miml)
