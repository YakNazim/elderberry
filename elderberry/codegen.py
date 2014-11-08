import yaml
import logging
from os import path
import pycparser
from pycparser import c_generator, c_ast
import pycparserext
from pycparserext.ext_c_parser import GnuCParser, AttributeSpecifier
from pycparserext.ext_c_generator import GnuCGenerator

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
            if not isinstance(n, AttributeSpecifier):
                continue
            if not isinstance(n.exprlist.exprs[0], c_ast.FuncCall):
                continue
            if n.exprlist.exprs[0].name.name != 'miml':
                continue
            args = self.get_args(node.type.args)
            mimltype = n.exprlist.exprs[0].args.exprs[0].name
            self.miml_funcs += [{'name': node.name,
                                 'file': node.coord.file,
                                 'type': mimltype,
                                 'args': args
                                }]

class Expand:
    def __init__(self, cppargs=''):
        # TODO: warn if c func return isn't right for the type
        self.cpp_args = cppargs.split() + [
            r'-DMIML_INIT=__attribute__((miml(init)))',
            r'-DMIML_FINAL=__attribute__((miml(final)))',
            r'-DMIML_SENDER=__attribute__((miml(sender)))',
            r'-DMIML_RECEIVER=__attribute__((miml(receiver)))'
        ]

    def handle(self, tree):
        self.includes = tree['include']
        tree['modules'] = {}
        for header in tree['headers']:
            pathname = self.findpath(header)
            fullpath = path.join(pathname, header)
            ast = pycparser.parse_file(fullpath, use_cpp=True, cpp_args=self.cpp_args, parser=GnuCParser())
            parsed = MimlCollector()
            parsed.visit(ast)

            funcs = [func for func in parsed.miml_funcs if func.pop('file') == fullpath]
            basename = header.split('.')[0]

            tree['modules'][basename] = {}
            for func in funcs:
                functype = func.pop('type')
                #FIXME: if there are more than one init or final
                if functype == 'init' or functype == 'final':
                    tree['modules'][basename][functype] = func['name']
                else:
                    try:
                        tree['modules'][basename][functype][func['name']] = func['args']
                    except KeyError:
                        tree['modules'][basename][functype] = {func['name']: func['args']}
            tree['modules'][basename]['object'] = basename + '.o'
            tree['modules'][basename]['file'] = header
            tree['modules'][basename]['path'] = pathname
            tree['modules'][basename]['fullpath'] = fullpath

    def findpath(self, filename):
        for pathname in self.includes:
            fullpath = path.join(pathname, filename)
            if path.exists(fullpath):
                return pathname
        else:
            raise IOError("Could not find header file: " + filename)

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
        headers = []
        for module in tree['modules'].values():
            headers.append(module['fullpath'])
        headers = ' '.join(headers)
        self.output.append("{}: {} {}".format(tree['codename'], tree['mainmiml'], headers))
        self.output.append('\t' + tree['framework'] + "/codeGen.py -c " + tree['mainmiml'])

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
        for header in tree['headers']:
            self.output.append('#include "{}"'.format(header))

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
        for parameter in tree['modules'][src]['sender'][func]:  # for each param in caller
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


class Parser:
    def __init__(self, config, modeflags):
        try:
            with open(config, 'r') as conf:
                self.config = yaml.load(conf)
        except IOError as e:
            logging.error("Opening config: " + str(e))
            raise
        except yaml.YAMLError as e:
            logging.error("YAML parsing error in config: " + str(e))
            raise

        try:
            self.modenames = self.config.pop('filenames', {})
            self.include = self.config.pop('include', [])
            self.framework = self.config.pop('framework', '.')
        except AttributeError:
            self.modenames={}
            self.include=[]
            self.framework='.'
        self.include += ['']

        self.handlers = [Expand(), Makefile(), Codefile()]

    def parse(self, mainmiml):
        try:
            with open(mainmiml, 'r') as miml:
                self.master = yaml.load(miml)
        except IOError as e:
            logging.error("Error opening main MIML file: " + str(e))
            raise
        except yaml.YAMLError as e:
            logging.error("YAML parsing error: " + str(e))
            raise
        self.master['mainmiml'] = mainmiml
        self.master['codename'] = self.modenames['code']
        self.master['framework'] = self.framework
        self.master['include'] = self.include
        for handler in self.handlers:
            handler.handle(self.master)
        self.handlers[1].dump(self.modenames['make'])
        self.handlers[2].dump(self.modenames['code'])

