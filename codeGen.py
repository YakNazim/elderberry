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
import sys
import re
import yaml
import copy
import fnmatch
import logging
from os import path, access, R_OK
from collections import defaultdict


class ErrorCounter(logging.Filter):
    warnings = 0
    errors = 0

    def filter(self, record):
        if record.levelname == 'WARNING':
            self.warnings += 1
        if record.levelname == 'ERROR':
            self.errors += 1
        return True

    def reset(self):
        self.warnings = 0
        self.errors = 0

def errorExit(msg, *args, **kwargs):
    logging.error(msg, *args, **kwargs)
    sys.exit(1)

class OutputGenerator:

    def __init__(self, modename, filename='', modeflag=False):
        self.output = defaultdict(str)
        self.filename = filename
        self.name = modename
        self.use = modeflag

    def append(self, level, data):
        self.output[level] += data + '\n'

    def display(self):
        if self.use:
            print(self.name, ": ", filename)
            for level in sorted(self.output):
                print (self.name, "->", level, "->", self.output[level])

    def write_out(self):
        if self.use:
            with open(self.filename, "w") as f:
                for level in sorted(self.output):
                    f.write(self.output[level])

class Parser:

    def __init__(self, config, modeflags):
        # Read config file.
        try:
            with open(config, 'r') as conf:
                self.config = yaml.load(conf)
        except IOError as e:
            errorExit("Opening config: " + str(e))
        except yaml.YAMLError as e:
            errorExit("YAML parsing error in config: " + str(e))

        # get filename configuration data and remove from config, this makes
        # it so only handler data is left. Better for handlers!
        try:
            self.modenames = self.config.pop('filenames', {})
            self.handler_paths = self.config.pop('handler_paths', {})
        except AttributeError:
            self.modenames={}
            self.handler_paths = {}

        self.errCount = ErrorCounter()
        logging.getLogger('').addFilter(self.errCount)

        # Setup a ParserHandlers objects
        # Since we have multiple MIML files now we need phases for processing.
        # Expansion allows handler functions that expect data in other files the opportunity
        #   to pull in that external data and place it in the parse tree.
        # Validation allows handler functions the opportunity to examine other data in the tree
        #   to ensure it is ready for use, including data pulled in by other functions.
        # Generate is where the actual parsing work happens, where handler functions generate output.
        # Actual output writing happens when all these phases are complete and is not part of "parsing".
        # There is a 4th stage (not really a stage), purge. In which a ParserHandlers function is called to
        # commit last minute stuff to the OutputGenerator. For some output requirements it may be easier to
        # stage to a local ParserHandler structure in Parse, then stage later.
        self.handler_states = [Expand(self), Validate(self), Generate(self)]
        self.handler_functions = ParseHandlers(self)
        self.output = {}
        for key, value in self.modenames:
            self.output[key] = OutputGenerator(key, value, modeflags[key])

    def parse(self, mainmiml):
        # top level 'public' function. Since we have external MIML docs we need to pull those in
        # before we crawl, so order of processing matters even though order of MIML elements does not.
        try:
            with open(mainmiml, 'r') as miml:
                self.master = yaml.load(miml)
        except IOError as e:
            errorExit("Error opening main MIML file: " + str(e))
        except yaml.YAMLError as e:
            errorExit("YAML parsing error: " + str(e))

        # Do Expand, Validate, Parse
        # Initialize the stage buffers
        self.buffer = self.master
        self.unhandled = {}
        for handler in self.handler_states:
            self.transition(handler)
            self.crawl(self.master)

        # purge staged data. Our 4th state, kinda...
        self.handler_functions.purge()

        # Make Output files!!!
        logging.debug(self.output.display())
        self.output.write_out()

    def transition(self, handler):
        state_name = handler.__class__.__name__
        # check for warnings and errors thrown during previous phase.
        if self.errCount.warnings > 0:
            print(self.errCount.warnings, " warning(s) encountered during ", state_name, "!")
        if self.errCount.errors > 0:
            print(self.errCount.errors, " error(s) encountered during ", state_name, "!")
            sys.exit(1)
        self.errCount.reset()

        if not self.unhandled == {}:
            errorExit("Unhandled MIML content at end of " +
                        state_name + " state!\n" + yaml.dump(self.unhandled))

        self.master = self.buffer
        self.unhandled = copy.copy(self.master)
        self.buffer = {}

        self.handler_functions = handler

        logging.debug(state_name + " This:")
        logging.debug(yaml.dump(self.master))

    def crawl(self, data, path=['']):
        # Recursive function "Weee!"
        # Different structure walking for dict/list/scalar
        # path works as stack of directories (push/pop)
        # FIXME: what if key/element is not str
        if isinstance(data, dict):
            for key, value in data.items():
                if self.handle(value, path + [key]) == False:
                    self.crawl(value, path + [key])
        elif isinstance(data, list):
            for element in data:
                if self.handle(element, path + [element]) == False:
                    self.crawl(element, path + [element])
        else:
            self.handle(data, path)

    def handle(self, data, path):
        # This method returns True if a handler decides no other parsing is required for
        # the data it handles, for the mode it is in.
        return_value = False
        for key, value in self.handler_paths.items():
            if fnmatch.fnmatchcase('/'.join(path), value['path']):
                if type(data).__name__ == self.handler_paths[key]['type']:
                    return_value = return_value or getattr(self.handler_functions, key)(data)
                else:
                    logging.error("Handler type mismatch. {} expects {}, received {}".format(key, self.handler_paths[key]['type'], type(data).__name__))

        return return_value

class ParseHandlers:

    def __init__(self, parser):
        self.parser = parser
        self.code = self.parser.output['code']
        self.make = self.parser.output['make']
        self.header = self.parser.output['header']

    def purge(self):
        # Required function, not part of config-based handlers
        # Called after Parsing phase, allows handlers to stage data and then commit to OutputGenerator after parse stage.
        # or allows single time setup data, like fcfutils.h include, or carriage returns for pretty output.
        self.code.append(6, "\n")
        self.code.append(11, "\n")
        self.code.append(16, "\n")
        self.code.append(101, "\n")
        self.make.append(6, "\n")

    def sources(self, data):
        return True  # Nothing responds to data under here, left in so includes/final can figure out what order to stage data.

    def messages(self, data):
        return False

    def modules(self, data):
        # Must return False or other module matches will not happen.
        self.parser.buffer['modules'] = data
        return False

    def includes(self, data):
        return True

    def objects(self, data):
        return True

    def inits(self, data):
        return True

    def init_final(self, data):
        return True

    def finals(self, data):
        return True

    def senders(self, data):
        # validate_params wrapper that targets senders
        return self.params(data)

    def receivers(self, data):
        # validate_params wrapper that targets receivers
        return self.params(data)

    def params(self, data):
        return True

class Expand(ParseHandlers):
    def sources(self, data):
        p = self.parser
        # Pull in external file data, place in buffer
        del(p.unhandled['sources'])
        p.buffer['modules'] = {}
        p.buffer['source_order'] = data
        for source in data:
            try:
                with open(source[1], 'r') as module:
                    p.buffer['modules'][source[0]] = yaml.load(module)
            except IOError as e:
                logging.error("Error opening module MIML file: " + str(e))
            except yaml.YAMLError as e:
                logging.error("YAML parsing error: " + str(e))

        return True

    def messages(self, data):
        # Nothing to expand, but buffer messages for later passes.
        del(self.parser.unhandled['messages'])
        self.parser.buffer['messages'] = data
        return True

class Validate(ParseHandlers):
    def messages(self, data):
        p = self.parser
        for message in data.keys():
            sender = message.split('.')
            if not len(sender) == 2:
                logging.error("Illegal Sender syntax: " + message)
            elif not sender[0] in p.master['modules']:
                logging.error("Sending source " + sender[0] + " not loaded as module.")
            elif not sender[1] in p.master['modules'][sender[0]]['senders']:
                logging.error("Sending message " + sender[1] + " not defined as sender for " + sender[0])
            else:
                sender_params = p.master['modules'][sender[0]]['senders'][sender[1]]
                for rec in data[message]:
                    receiver = rec.split('.')
                    if not len(sender) == 2:
                        logging.error("Illegal Receiver syntax: " + rec + " for message " + message)
                    elif not receiver[0] in p.master['modules']:
                        logging.error("Receiver: " + receiver[0] + " not loaded as module.")
                    elif not receiver[1] in p.master['modules'][receiver[0]]['receivers']:
                        logging.error("Receiver function " + receiver[1] + " not defined as receiver for " + receiver[0])
                    elif not len(sender_params) == len(p.master['modules'][receiver[0]]['receivers'][receiver[1]]):
                        logging.error("Message " + str(sender) + " cannot send to receiver " + str(rec) +
                        ". Number of arguments must be the same in both functions.")
                    else:
                        pos = 0
                        for param in sender_params:
                            if not param[1] == p.master['modules'][receiver[0]]['receivers'][receiver[1]][pos][1]:
                                logging.error("Message " + message + " cannot send to receiver " +
                                rec + ". Type mismatch on argument " + str(pos + 1))
                            pos += 1
        del(p.unhandled['messages'])
        p.buffer['messages'] = data
        return True

    def modules(self, modules):
        p = self.parser
        for name, body in modules.items():
            for key in body:
                if not key in ('include', 'object', 'init', 'final', 'senders', 'receivers'):
                    logging.error("Module: " + name + " contains illegal component: " + key)
        del(p.unhandled['modules'])
        p.buffer['modules'] = modules
        # Must return False or other module matches will not happen.
        return False

    def includes(self, data):
        # handles include files.
        if not re.match(r"\w+\.h", data):
            logging.error("Illegal header file format: " + data)
        return True

    def objects(self, data):
        # handles object files for the make file, needs to add 1 row to make file so stages
        # into (self.objects), purge makes output.
        if not re.match(r"(/|\w)+\.o", data):
            logging.error("Illegal object file format: " + data)
        return True

    def inits(self, data):
        # validates a modules initialize functions, output is generated via the module handler.
        if not re.match(r"\w+", data):
            logging.error("Illegal initialize function: " + data)
        return True

    def init_final(self, data):
        p = self.parser
        del(p.unhandled['source_order'])
        p.buffer['source_order'] = data
        p.buffer['mainfunc'] = []
        return True

    def finals(self, data):
        # validates a modules finalize functions, output is generated via the module handler.
        if not re.match(r"\w+", data):
            logging.error("Illegal finalize function: " + data)
        return True

    def params(self, data):
        # Validate sender and receiver parameters, checks that each parameter has 2 elements
        # and that the second could be a C type
        for param in data:
            if not len(param) == 2:
                logging.error("Illegal parameter definition: " + str(param))
            datatype = re.match(r"(?:const\s)?((?:unsigned\s)?\w+)(?:\s?[*&])?", param[1]).group(1)  # FIXME: This doesn't look like it hits all the types
            if not datatype:
                logging.error("Illegal parameter type: " + str(param[1]))
        return True

class Generate(ParseHandlers):

    def sources(self, data):
        p = self.parser
        module_miml = []
        for source in data:
            module_miml.append(source[1])
        self.make.append(10, self.code.filename + " " + self.header.filename + ": " + p.miml_file + " " + ' '.join(module_miml))
        self.make.append(10, "\t./codeGen.py -ch " + p.miml_file)
        return True  # Nothing responds to data under here, left in so includes/final can figure out what order to stage data.

    def messages(self, data):
        p = self.parser
        for message in data.keys():  # for each message
            (src, func) = message.split('.')
            args = []
            params = []
            types = []
            for caller_param in p.master['modules'][src]['senders'][func]:  # for each param in caller
                args.append(caller_param[1] + " " + caller_param[0])
                params.append(caller_param[0])
                types.append(caller_param[1])
            self.header.append(10, "void " + func + "(" + ', '.join(types) + ');')
            self.code.append(20, "void " + func + "(" + ', '.join(args) + ') {')
            for receivers in data[message]:  # for each receiver
                (rsrc, rfunc) = receivers.split('.')
                self.code.append(20, "    " + rfunc + "(" + ', '.join(params) + ');')
            self.code.append(20, "}\n")
        return True

    def includes(self, data):
        # handles include files.
        self.code.append(5, "#include \"" + data + "\"")
        return True

    def objects(self, data):
        # handles object files for the make file. Gives each object its own row
        self.make.append(5, "OBJECTS += " + data)
        return True

    def init_final(self, data):
        p = self.parser
        finals = []
        self.code.append(10, "void modules_initialize(struct ev_loop * loop) {")
        for source in data:
            token = source[0]
            if 'init' in p.master['modules'][token]:
                self.code.append(10, "    " + p.master['modules'][token]['init'] + "(loop);")
            if "final" in p.master['modules'][token]:
                self.code.append(10, "    atexit("+p.master['modules'][token]['final']+');')
        self.code.append(10, "}")
        return True

    def main(self, data):
        self.code.append(5, """
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ev.h>
""")

        # FIXME: escaped newlines
        self.code.append(100, """
static void stop_cb(struct ev_loop *loop, ev_signal *w, int revents){
    printf("Quitting\\n");
    ev_break(loop, EVBREAK_ALL);
}

int main(int argc, char *argv[]){
    //todo: boilerplate
    //todo: ev_version check, ev_backends check

    struct ev_loop * loop;
    loop = ev_default_loop(0);
    if(!loop){
        fprintf(stderr, "Fatal: could not initialize libev\\n");
        return EXIT_FAILURE;
    }

    ev_signal stop;
    ev_signal_init(&stop, stop_cb, SIGINT);
    ev_signal_start(loop, &stop);
    //todo: argc, argv passed to initialize. Use argp?
    modules_initialize(loop);
    ev_run (loop, 0);


    return EXIT_SUCCESS;
}""")

        return True

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', help='Generate C files', action='store_true')
    argparser.add_argument('-m', help='Generate Makefiles', action='store_true')
    argparser.add_argument('-b', help='Do something with headers', action='store_true')
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
    modeflags['header'] = args.b

    config = args.g if args.g else 'cg.conf'

    parser = Parser(config, modeflags)
    parser.parse(args.miml)
