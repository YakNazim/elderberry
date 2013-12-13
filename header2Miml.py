#!/usr/bin/python

#     Assumptions:
#         - only parses extern functions
#         - init/final functions only detected with "initialize" and "finalize" in name
#         - any non-init/final functions with "initialize" or "finalize" aren't included
#         - only data types recognized are [const|unsigned] [int|char]
#         - variable names not defined are replaced by ARG# variable name

import sys, re
import argparse

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('header', help='C header to convert to a MIML module')
    argparser.add_argument('modulename', nargs='?', help='Name of the MIML module file. Defaults to Header name')
    args = argparser.parse_args()

    if not args.header.endswith('.h'):
        print "Error: Input file not a .h file."
        sys.exit(-1)
    basename = args.header[:-2]

    inputfile = basename + '.h'
    objfile = basename + '.o'

    if not args.modulename:
        outputfile = basename + '.miml'
    elif args.modulename.endswith('.miml'):
        outputfile = args.modulename
    else:
        print "Error: Output file not a .miml file."
        sys.exit(-1)

    try:
        f = open(inputfile, 'r')
    except IOError as e:
        print "I/O error({0}): Input header file --> {1}".format(e.errno, e.strerror)
        sys.exit(-1)

    codeLines = f.readlines()
    f.close()

    try:
        f = open('cg.conf', 'r')
    except IOError as e:
        print "I/O error({0}): cg.conf --> {1}".format(e.errno, e.strerror)
        sys.exit(-1)

    cgConf = f.readlines()
    f.close()

    for item in cgConf:
        match = re.match(r'[\s]*allowed_types: \[(.*)\][\s]*', item, re.M | re.I)
        if match:
            allowedTypes = match.group(1)
            allowedTypes = re.sub(r"\,[\s]*", "|", allowedTypes)
            allowedTypes = re.sub(r"'", "", allowedTypes)
            allowedTypes = re.sub(r"(const|unsigned)[\s]+", "", allowedTypes)
            break


    outputCodeHeader = "%YAML 1.2\n---\ninclude: " + inputfile + "\nobject: " + objfile
    outputCodeInit = "init: "
    outputCodeFinal = "final: "
    outputCodeSenders = "# Functions that handle outgoing data\nsenders:\n"
    outputCodeReceivers = "# Functions that handle incoming data\nreceivers:\n"
    outputCodeUnknown = "[unknown:]\n"
    foundInit = 0
    foundFinal = 0
    foundUnknown = 0
    foundSenders = 0
    foundReceivers = 0

    def xstr(s):
        if s is None:
            return ''
        return str(s)

    for item in codeLines:
        # match = re.match( r'[\s]*(extern[\s]+)?([\w]+[\s]+)([\w_-]+)[\s]*\((.*)\).*', item.strip('\n'), re.M|re.I)
        match = re.match(r'[\s]*(extern[\s]+)?([\w]+[\s]+)([\w_-]+)[\s]*\((.*)\)[\s]*;[\s]*(\/\/[\s]*\[[\s]*miml[\s]*:[\s]*(init|final|sender|receiver)[\s]*\])?.*', item.strip('\n'), re.M | re.I)
        if match:
            mimlType = match.group(6)
            if(mimlType == "init"):
                outputCodeInit += str(match.group(3)) + "();"
                foundInit += 1
                continue

            if(mimlType == "final"):
                outputCodeFinal += str(match.group(3)) + "();"
                foundFinal += 1
                continue

            content = match.group(4).split(',')
            counter = 0

            argVals = ""
            for item2 in content:
                counter += 1
                match2 = re.match(r'[\s]*((const|unsigned)[\s]+)?(' + allowedTypes + ')[\s]*(\*)?([\s]*([\w_-]+)[\s]*)?', item2, re.M | re.I)
                if match2:
                    argType = xstr(match2.group(1)) + xstr(match2.group(3)) + xstr(match2.group(4))
                    argName = match2.group(6)
                    if argName is None:
                        argName = "ARG" + str(counter)

                    argVals += "  - [" + argName + ", " + argType.strip() + "]\n"

            funcName = str(match.group(3))
            if (mimlType == "receiver"):
                outputCodeReceivers += "  " + funcName + ":\n" + argVals
                foundReceivers += 1
            elif (mimlType == "sender"):
                outputCodeSenders += "  " + funcName + ":\n" + argVals
                foundSenders += 1
            else:
                outputCodeUnknown += "  " + funcName + ":\n" + argVals
                foundUnknown += 1

    try:
        fout = open(outputfile, 'w')
    except IOError as e:
        print "I/O error({0}): Output Miml file --> {1}".format(e.errno, e.strerror)
        sys.exit(-1)
    fout.write(outputCodeHeader + "\n")
    if(foundInit):
        fout.write(outputCodeInit + "\n")
    if(foundFinal):
        fout.write(outputCodeFinal + "\n\n")
    else:
        fout.write("\n")
    fout.write(outputCodeSenders + "\n")
    fout.write(outputCodeReceivers + "\n")
    # if foundUnknown:
    #     fout.write("# Functions that have not been designated as\n")
    #     fout.write("# senders or receivers. Sort them accordingly\n")
    #     fout.write("# and delete the [unknown:] header.\n")
    #     fout.write(outputCodeUnknown + "\n")
    fout.close()

    print "\n " + inputfile + "  ->  " + outputfile
    print "======================================================"
    # print " Init\tFinal\tSenders\t  Receivers   Unknown             "
    print " Init\tFinal\tSenders\t  Receivers                     "
    print "------------------------------------------------------"
    # print " " + str(foundInit) + "\t" + str(foundFinal) + "\t" + str(foundSenders) + "\t  " + str(foundReceivers) + "\t      " + str(foundUnknown)
    print " " + str(foundInit) + "\t" + str(foundFinal) + "\t" + str(foundSenders) + "\t  " + str(foundReceivers)
    print ""
