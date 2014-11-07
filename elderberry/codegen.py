import sys
import re
import yaml
import copy
import fnmatch
import logging
from os import path, access, R_OK
from collections import defaultdict
from pprint import pprint

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
        print(self.name, ": ", self.filename)
        for level in sorted(self.output):
            print (self.output[level])

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

        try:
            self.modenames = self.config.pop('filenames', {})
            self.include_dirs = self.config.pop('include', [])
        except AttributeError:
            self.modenames={}
            self.include_dirs=[]
        self.include_dirs += ['']

        self.errCount = ErrorCounter()
        logging.getLogger('').addFilter(self.errCount)

        self.output = {}
        for key, value in self.modenames.items():
            self.output[key] = OutputGenerator(key, value, modeflags[key])

        self.handler_states = [Expand(self.include_dirs), Makefile(self.output['make']), Codefile(self.output['code'])]

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
        self.master['mainmiml'] = mainmiml
        self.master['codename'] = self.modenames['code']

        for handler in self.handler_states:
            print("Now entering:", handler.__class__.__name__)
            handler.handle(self.master)
            self.check(handler)
        #self.output.write_out()

    def check(self, handler):
        state_name = handler.__class__.__name__
        # check for warnings and errors thrown during previous phase.
        if self.errCount.warnings > 0:
            print(self.errCount.warnings, " warning(s) encountered during ", state_name, "!")
        if self.errCount.errors > 0:
            print(self.errCount.errors, " error(s) encountered during ", state_name, "!")
            sys.exit(1)
        self.errCount.reset()

class Expand:
    def __init__(self, includes):
        self.includes = includes

    def handle(self, tree):
        tree['modules'] = {}
        for miml in tree['sources']:
            tree['modules'][miml[0]] = self.expand(miml[1])

    def expand(self, filename):
        for pathname in self.includes:
            fullpath = path.join(pathname, filename)
            if path.exists(fullpath):
                try:
                    with open(fullpath, 'r') as f:
                       return yaml.load(f)
                except IOError as e:
                    logging.error("Error opening module MIML file: " + str(e))
                except yaml.YAMLError as e:
                    logging.error("YAML parsing error: " + str(e))
                break
        else:
            logging.error("Could not find module MIML file: " + filename)

class Makefile:
    def __init__(self, output):
        self.make = output

    def handle(self, tree):
        self.sources(tree, tree['sources'])
        for source in tree['modules'].values():
            self.objects(source['object'])
        self.make.append(6, "\n")

    def sources(self, tree, data):
        module_miml = []
        for source in data:
            module_miml.append(source[1])
        self.make.append(10, "{}: {} {}".format(tree['codename'], tree['mainmiml'], ' '.join(module_miml)))
        self.make.append(10, "\t./codeGen.py -ch " + tree['mainmiml'])

    def objects(self, data):
        self.make.append(5, "OBJECTS += " + data)

class Codefile:
    def __init__(self, output):
        self.code = output

    def handle(self, tree):
        for sender, receivers in tree['messages'].items():
            self.messages(tree, sender, receivers)
        for module in tree['modules'].values():
            self.includes(module['include'])

        self.init_final(tree['modules'].values())
        self.main()

    def messages(self, tree, sender, receivers):
        src, func = sender.split('.')
        args = []
        params = []
        i = 0
        for parameter in tree['modules'][src]['senders'][func]:  # for each param in caller
            if len(parameter) == 2:
                args.append(parameter[1] + " " + parameter[0])
                params.append(parameter[0])
            else:
                args.append(parameter[0] + ' ' + '_arg' + str(i))
                params.append('_arg' + str(i))
                i += 1
        self.code.append(20, 'void '+func+'('+', '.join(args)+') {')
        for receiver in receivers:
            rsrc, rfunc = receiver.split('.')
            self.code.append(20, '    {}({});'.format(rfunc, ', '.join(params)))
        self.code.append(20, "}\n")

    def includes(self, data):
        self.code.append(5, '#include "{}"'.format(data))

    def init_final(self, sources):
        self.code.append(10, "void modules_initialize(struct ev_loop * loop) {")
        for source in sources:
            if 'init' in source:
                self.code.append(10, "    "+source['init']+"(loop);")
            if "final" in source:
                self.code.append(10, "    atexit("+source['final']+');')
        self.code.append(10, "}")

    def main(self):
        # FIXME: template
        self.code.append(2, """
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <ev.h>
""")

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

