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

import sys
import argparse
import re
import yaml
import copy
from os import path, access, R_OK
import fnmatch
from collections import defaultdict

class ErrorLogger:
    # Log errors or warnings here, then check periodically.
    # Code Generator uses no warnings, but they can be fun for debugging.
    # The check method exits if errors exist, but just prints out warnings and keeps going.
    def __init__(self):
        self.errors = []
        self.warnings = []

    def new_error(self, message):
        self.errors.append(message)

    def new_warning(self, message):
        self.warnings.append(message)

    def append_error(self, message):
        if len(self.errors) > 0:  # append to empty list just adds new error.
            message = self.errors.pop() + message
        self.errors.append(message)

    def append_warnings(self, message):
        if len(self.warnings) > 0:  # append to empty list just adds new error.
            message = self.warnings.pop() + message
        self.warnings.append(message)

    def has_errors(self):
        if len(self.errors) > 0:
            return True
        return False

    def has_warnings(self):
        if len(self.warnings) > 0:
            return True
        return False

    def check(self):
        if self.has_warnings():
            print (len(self.warnings), " warning(s) encountered!")
            for warning in self.warnings:
                print (warning)
        if self.has_errors():
            print (len(self.errors), " error(s) encountered!")
            for error in self.errors:
                print (error)
            sys.exit(0)

class OutputGenerator:
    # What we want here is:
    #    RootDictionary { ModeDictionary { LevelDictionary { OutputList [] }}}
    #
    # So OutputGen{Code}{1}{Include File1, Include File2}
    # or OutputGen{Header1}{1}{Function PrototypeA, Function PrototypeB}
    #
    # This way different Handlers can be invoked for different purposes
    #   and order their output as they wish.
    # The constructor strucure mode_flages_files should coincide with the modes allowed.
    # So if you add to one add to the other. Same mode token, its used across them in the boolean run check!

    def __init__(self, mode_flags_files):
        self.output = defaultdict(lambda: defaultdict(list))
        self.mode_flags_files = mode_flags_files

    def append(self, mode, level, data):
        self.output[mode][level].append(data)

    def display(self):
        for mode in self.output.keys():
            if self.mode_flags_files[mode]['run'] == True:
                print (mode + ": " + self.mode_flags_files[mode]['file'])
                for level in sorted(self.output[mode].keys()):
                    for message in self.output[mode][level]:
                        print (mode, "->", level, "->", message)
            print ("\n")  # separate modes

    def write_out(self):
        for mode in self.output.keys():
            if self.mode_flags_files[mode]['run'] == True:
                f = open(self.mode_flags_files[mode]['file'], "w")
                for level in sorted(self.output[mode].keys()):
                    for message in self.output[mode][level]:
                        f.write(message + '\n')

class Parser:

    def __init__(self, config, mainmiml, modeflages):
        self.errors = ErrorLogger()
        # declare modes_flags_files
        modes_flags_files = {'code': {'run': modeflags['c'], 'file': None},
                             'make': {'run': modeflags['m'], 'file': None},
                             'header': {'run': modeflags['b'], 'file': None}}

        # Read config file.
        self.miml_file = mainmiml

        try:
            with open(config, 'r') as conf:
                self.config = yaml.load(conf)
        except OSError as e:
            self.errors.new_error("Error opening config file: " + str(e))
        except yaml.YAMLError as e:
            self.errors.new_error("YAML parsing error: " + str(e))
        self.errors.check()

        # get filename configuration data and remove from config, this makes
        # it so only handler data is left. Better for handlers!
        modes_flags_files['code']['file'] = self.config.pop('code_filename')
        modes_flags_files['header']['file'] = self.config.pop('header_filename')
        modes_flags_files['make']['file'] = self.config.pop('make_filename')

        # Frameworkinclude_dirs location
        framework_dir = self.config.pop('framework_dir', '')

        # Setup a ParserHandlers objects
        # Since we have multiple MIML files now we need phases for processing.
        # Expansion allows handler functions that expect data in other files the opportunity
        #   to pull in that external data and place it in the parse tree.
        # Validation allows handler functions the opportunity to examine other data in the tree
        #   to ensure it is ready for use, including data pulled in by other functions.
        # Parsing is where the actual parsing work happens, where handler functions generate output.
        # Actual output writing happens when all these phases are complete and is not part of "parsing".
        # There is a 4th stage (not really a stage), purge. In which a ParserHandlers function is called to
        # commit last minute stuff to the OutputGenerator. For some output requirements it may be easier to
        # stage to a local ParserHandler structure in Parse, then stage later.
        self.handler_states = [Expand(self, framework_dir),
                               Validate(self, framework_dir),
                               Parse(self, framework_dir)]
        self.handler_functions = ParseHandlers(self, framework_dir)

        self.output = OutputGenerator(modes_flags_files)

    def parse(self):
        # top level 'public' function. Since we have external MIML docs we need to pull those in
        # before we crawl, so order of processing matters even though order of MIML elements does not.
        try:
            with open(self.miml_file, 'r') as mainmiml:
                self.master = yaml.load(mainmiml)
        except OSError as e:
            self.errors.new_error("Error opening main MIML file: " + str(e))
        except yaml.YAMLError as e:
            self.errors.new_error("YAML parsing error: " + str(e))
        self.errors.check()

        # Do Expand, Validate, Parse
        # Initialize the stage buffers
        self.buffer = self.master
        self.unhandled = {}
        for handler in self.handler_states:
            self.transition(handler)
            self.crawl(self.master)

        # purge staged data. Our 4th state, kinda...
        self.handler_functions.purge()
        # Output
        # Let's you see stuff, uncomment when writing MIML extensions and trying to
        # figure out where to insert content in OutputGenerator.
        # self.output.display()
        # Make files!!!
        self.output.write_out()

    def transition(self, handler):
        state_name = handler.__class__.__name__
        # check for errors thrown during previous phase.
        self.errors.check()
        if not self.unhandled == {}:
            self.errors.new_error("Unhandled MIML content at end of " +
                        state_name + " state!\n" + yaml.dump(self.unhandled))

        self.master = self.buffer
        self.unhandled = copy.copy(self.master)
        self.buffer = {}

        handler.object_names = self.handler_functions.object_names
        self.handler_functions = handler

        # todo: logger.debug
        # print (state_name + " This:")
        # print (yaml.dump(self.master))

        # Check for errors thrown during transition
        self.errors.check()

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
        for key, value in self.config.items():
            # match current location to a handler path
            if fnmatch.fnmatchcase('/'.join(path), value['path']):
                # verify data type is correct
                if type(data).__name__ == self.config[key]['type']:
                    # call hander function 'key', in ParserHandlers, passing data
                    return_value = return_value or getattr(self.handler_functions, key)(data)
                else:
                    # type of data is not same as what was declared in cg.conf, so error.
                    self.errors.new_error("Handler type mismatch. " + key + " expects " + self.config[key]['type'] + ", received " + type(data).__name__)

        return return_value

class ParseHandlers:

    def __init__(self, parser, framework_dir):
        self.parser = parser
        # to support validate_params
        self.framework_dir = framework_dir

        # objects for single line make file
        self.object_names = []

    def purge(self):
        # Required function, not part of config-based handlers
        # Called after Parsing phase, allows handlers to stage data and then commit to OutputGenerator after parse stage.
        # or allows single time setup data, like fcfutils.h include, or carriage returns for pretty output.
        o = self.parser.output
        o.append("code", 6, "\n")
        o.append("code", 11, "\n")
        o.append("code", 16, "\n")
        o.append("code", 101, "\n")
        o.append("make", 6, "\n")
        if len(self.object_names) > 0:
            self.parser.output.append("make", 5, "OBJECTS += " + ' '.join(self.object_names))

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
        e = p.errors
        # Pull in external file data, place in buffer
        del(p.unhandled['sources'])
        p.buffer['modules'] = {}
        p.buffer['source_order'] = data
        for source in data:
            try:
                with open(source[1], 'r') as module:
                    p.buffer['modules'][source[0]] = yaml.load(module)
            except OSError as e:
                e.new_error("Error opening module MIML file: " + str(e))
            except yaml.YAMLError as e:
                e.new_error("YAML parsing error: " + str(e))

        return True

    def messages(self, data):
        # Nothing to expand, but buffer messages for later passes.
        del(self.parser.unhandled['messages'])
        self.parser.buffer['messages'] = data
        return True

class Validate(ParseHandlers):
    def messages(self, data):
        p = self.parser
        e = p.errors
        for message in data.keys():
            sender = message.split('.')
            if not len(sender) == 2:
                e.new_error("Illegal Sender syntax: " + message)
            elif not sender[0] in p.master['modules']:
                e.new_error("Sending source " + sender[0] + " not loaded as module.")
            elif not sender[1] in p.master['modules'][sender[0]]['senders']:
                e.new_error("Sending message " + sender[1] + " not defined as sender for " + sender[0])
            else:
                sender_params = p.master['modules'][sender[0]]['senders'][sender[1]]
                for rec in data[message]:
                    receiver = rec.split('.')
                    if not len(sender) == 2:
                        e.new_error("Illegal Receiver syntax: " + rec + " for message " + message)
                    elif not receiver[0] in p.master['modules']:
                        e.new_error("Receiver: " + receiver[0] + " not loaded as module.")
                    elif not receiver[1] in p.master['modules'][receiver[0]]['receivers']:
                        e.new_error("Receiver function " + receiver[1] + " not defined as receiver for " + receiver[0])
                    elif not len(sender_params) == len(p.master['modules'][receiver[0]]['receivers'][receiver[1]]):
                        e.new_error("Message " + str(sender) + " cannot send to receiver " + str(rec) +
                        ". Number of arguments must be the same in both functions.")
                    else:
                        pos = 0
                        for param in sender_params:
                            if not param[1] == p.master['modules'][receiver[0]]['receivers'][receiver[1]][pos][1]:
                                e.new_error("Message " + message + " cannot send to receiver " +
                                rec + ". Type mismatch on argument " + str(pos + 1))
                            pos += 1
        del(p.unhandled['messages'])
        p.buffer['messages'] = data
        return True

    def modules(self, modules):
        p = self.parser
        e = p.errors
        for name, body in modules.items():
            for key in body:
                if not key in ('include', 'object', 'init', 'final', 'senders', 'receivers'):
                    e.new_error("Module: " + name + " contains illegal component: " + key)
        del(p.unhandled['modules'])
        p.buffer['modules'] = modules
        # Must return False or other module matches will not happen.
        return False

    def includes(self, data):
        # handles include files.
        p = self.parser
        e = p.errors
        if not re.match(r"\w+\.h", data):
            e.new_error("Illegal header file format: " + data + " in " + '/'.join(p.path))
        return True

    def objects(self, data):
        # handles object files for the make file, needs to add 1 row to make file so stages
        # into (self.objects), purge makes output.
        p = self.parser
        e = p.errors
        if not re.match(r"(/|\w)+\.o", data):
            e.new_error("Illegal object file format: " + data + " in " + '/'.join(p.path))
        return True

    def inits(self, data):
        # validates a modules initialize functions, output is generated via the module handler.
        p = self.parser
        e = p.errors
        if not re.match(r"\w+\([^)]*\);", data):
            e.new_error("Illegal initialize function: " + data + " in " + '/'.join(p.path))
        return True

    def init_final(self, data):
        p = self.parser
        del(p.unhandled['source_order'])
        p.buffer['source_order'] = data
        p.buffer['mainfunc'] = []
        return True

    def finals(self, data):
        # validates a modules finalize functions, output is generated via the module handler.
        p = self.parser
        e = p.errors
        if not re.match(r"\w+\([^)]*\);", data):
            e.new_error("Illegal finalize function: " + data + " in " + '/'.join(p.path))
        return True

    def params(self, data):
        # Validate sender and receiver parameters, checks that each parameter has 2 elements
        # and that the second could be a C type
        p = self.parser
        e = p.errors
        for param in data:
            if not len(param) == 2:
                e.new_error("Illegal parameter definition: " + str(param) + " in " + '/'.join(p.path))
            datatype = re.match(r"(?:const\s)?((?:unsigned\s)?\w+)(?:\s?[*&])?", param[1]).group(1)  # FIXME: This doesn't look like it hits all the types
            if not datatype:
                e.new_error("Illegal parameter type: " + str(param[1]) + " in " + '/'.join(p.path))
        return True

class Parse(ParseHandlers):

    def sources(self, data):
        p = self.parser
        o = p.output

        module_miml = []
        for source in data:
            module_miml.append(source[1])
        o.append("make", 10, o.mode_flags_files['code']['file'] + " " + o.mode_flags_files['header']['file'] + ": " + p.miml_file + " " + ' '.join(module_miml))
        o.append("make", 10, "\t./codeGen.py -ch " + p.miml_file)
        return True  # Nothing responds to data under here, left in so includes/final can figure out what order to stage data.

    def messages(self, data):
        p = self.parser
        o = p.output
        for message in data.keys():  # for each message
            (src, func) = message.split('.')
            args = []
            params = []
            types = []
            for caller_param in p.master['modules'][src]['senders'][func]:  # for each param in caller
                args.append(caller_param[1] + " " + caller_param[0])
                params.append(caller_param[0])
                types.append(caller_param[1])
            o.append("header", 10, "void " + func + "(" + ', '.join(types) + ');')
            o.append("code", 20, "void " + func + "(" + ', '.join(args) + ') {')
            for receivers in data[message]:  # for each receiver
                (rsrc, rfunc) = receivers.split('.')
                o.append("code", 20, "    " + rfunc + "(" + ', '.join(params) + ');')
            o.append("code", 20, "}\n")
        return True

    def includes(self, data):
        # handles include files.
        p = self.parser
        o = p.output
        o.append("code", 5, "#include \"" + data + "\"")
        return True

    def objects(self, data):
        # handles object files for the make file, needs to add 1 row to make file so stages
        # into (self.object_names), purge makes output.
        self.object_names.append(data)
        return True

    def init_final(self, data):
        p = self.parser
        o = p.output
        finals = []
        o.append("code", 10, "int modules_initialize(struct ev_loop * loop) {")
        for source in data:
            token = source[0]
            if 'init' in p.master['modules'][token]:
                o.append("code", 10, "    " + p.master['modules'][token]['init'])
            if "final" in p.master['modules'][token]:
                finals.append(p.master['modules'][token]['final'])
        o.append("code", 10, "    return 1;\n}")
        o.append("code", 15, "void modules_finalize(struct ev_loop * loop) {")
        while len(finals) > 0:
            o.append("code", 15, "    " + finals.pop())
        o.append("code", 15, "}")
        return True

    def main(self, data):
        o = self.parser.output
        o.append("code", 5, """
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ev.h>
""")

        # FIXME: escaped newlines
        o.append("code", 100, """
static void stop_cb(struct ev_loop *loop, ev_signal *w, int revents){
    printf("Quitting\\n");
    ev_break(loop, EVBREAK_ALL);
}

int main(int argc, char *argv[]){
    //todo: boilerplate
    //todo: ev_version check, ev_backends check

    int retval = EXIT_SUCCESS;

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
    if(modules_initialize(loop)){
        fprintf(stderr, "Fatal: module initialization failure\\n");
        retval = EXIT_FAILURE;
    }else{
        ev_run (loop, 0);
    }
    modules_finalize(loop);

    return retval;
}""")

        return True


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-c', help='c files?', action='store_true')
    argparser.add_argument('-m', help='makefiles?', action='store_true')
    argparser.add_argument('-b', help='headers?', action='store_true')
    argparser.add_argument('miml', help='Main miml filename')
    args = argparser.parse_args()

    modeflags = {}
    modeflags['c'] = args.c
    modeflags['m'] = args.m
    modeflags['b'] = args.b
    parser = Parser('cg.conf', args.miml, modeflags)
    parser.parse()
