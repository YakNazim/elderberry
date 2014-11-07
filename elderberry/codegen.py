import sys
import yaml
import logging
from os import path
import pycparser
from pycparser import c_generator, c_ast
import pycparserext
from pycparserext.ext_c_parser import GnuCParser, AttributeSpecifier
from pycparserext.ext_c_generator import GnuCGenerator

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


class WriteMiml:

    def __init__(self, funcs, basename):
        header = basename + '.h'
        objfile = basename + '.o'
        self.outputfile = basename + '.miml'

        output = {'include': header, 'object': objfile, 'senders': {}, 'receivers': {}}
        for func in funcs:
            if func['file'] != args.header:
                continue

            if func['type'] == 'init':
                output['init'] = func['name']
            elif func['type'] == "final":
                output['final'] = func['name']
            elif func['type'] == 'receiver':
                output['receivers'][func['name']] = func['args']
            elif func['type'] == 'sender':
                output['senders'][func['name']] = func['args']

        self.output = output

    def dump(self):
        try:
            with open(self.outputfile, 'w') as fout:
                yaml.dump(self.output, fout, explicit_start=True)
        except IOError as e:
            print("I/O error({0}): Output Miml file --> {1}".format(e.errno, e.strerror))
            sys.exit(-1)

class MimlCollector(c_ast.NodeVisitor):
    def __init__(self):
        self.miml_funcs=[]

    def get_args(self, paramlist):
        args = []
        for node in paramlist.params:
            pointers = []
            while isinstance(node.type, c_ast.PtrDecl):
                pointers += ['*']
                node = node.type
            args += [[' '.join(node.type.type.names + pointers)]]
            if node.type.declname:
                args[-1].append(node.type.declname)
        return args

    def visit_Decl(self, node):
        for n in node.funcspec:
            if isinstance(n, AttributeSpecifier):
                if isinstance(n.exprlist.exprs[0], c_ast.FuncCall):
                    if n.exprlist.exprs[0].name.name == 'miml':
                        args = self.get_args(node.type.args)
                        mimltype = n.exprlist.exprs[0].args.exprs[0].name
                        self.miml_funcs += [{'name':node.name,
                                             'file': node.coord.file,
                                             'type': mimltype,
                                             'args':args
                                           }]

class HeaderParse:
    def __init__(self, filename, cppargs):

        # TODO: warn if c func return isn't right for the type
        cpp_args = cppargs.split() + [
            r'-DMIML_INIT=__attribute__((miml(init)))',
            r'-DMIML_FINAL=__attribute__((miml(final)))',
            r'-DMIML_SENDER=__attribute__((miml(sender)))',
            r'-DMIML_RECEIVER=__attribute__((miml(receiver)))'
        ]

        ast = pycparser.parse_file(filename, use_cpp=True, cpp_args=cpp_args, parser=GnuCParser())
        dv = MimlCollector()
        dv.visit(ast)
        self.funcs = dv.miml_funcs

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

        self.handler_states = [Expand(self.include_dirs), Makefile(), Codefile()]

    def parse(self, mainmiml):
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
        self.handler_states[1].dump(self.modenames['make'])
        self.handler_states[2].dump(self.modenames['code'])

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
    def __init__(self):
        self.output = []

    def dump(self, filename):
        print('\nGenerated File:', filename)
        for line in self.output:
            print(line)

    def handle(self, tree):
        for source in tree['modules'].values():
            self.output.append('OBJECTS += ' + source['object'])
        self.output.append('')
        header = []
        for source in tree['modules'].values():
            header.append(source['include'])
        header = ' '.join(header)
        self.output.append("{}: {} {}".format(tree['codename'], tree['mainmiml'], header))
        self.output.append("\t./codeGen.py -c " + tree['mainmiml'])

class Codefile:
    def __init__(self):
        self.output = []

    def dump(self, filename):
        print('\nGenerated File:', filename)
        for line in self.output:
            print(line)

    def handle(self, tree):
        # FIXME: template
        self.output.append('#include <stdlib.h>')
        self.output.append('#include <stdio.h>')
        self.output.append('#include <signal.h>')
        self.output.append('#include <ev.h>')
        for module in tree['modules'].values():
            self.output.append('#include "{}"'.format(module['include']))

        self.output.append('')
        self.output.append("void modules_initialize(struct ev_loop * loop) {")
        for source in tree['modules'].values():
            if 'init' in source:
                self.output.append("    "+source['init']+"(loop);")
            if "final" in source:
                self.output.append("    atexit("+source['final']+');')
        self.output.append("}")

        self.output.append('')
        for sender, receivers in tree['messages'].items():
            self.messages(tree, sender, receivers)

        self.output.append('')
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
        self.output.append('void '+func+'('+', '.join(args)+') {')
        for receiver in receivers:
            rsrc, rfunc = receiver.split('.')
            self.output.append('    {}({});'.format(rfunc, ', '.join(params)))
        self.output.append("}")

    def main(self):
        self.output.append("""
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

