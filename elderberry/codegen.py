import yaml
import logging
from os import path
from string import Template
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
    def __init__(self, filename='', cppargs=''):
        # TODO: warn if c func return isn't right for the type
        self.cpp_args = cppargs.split() + [
            r'-DMIML_INIT=__attribute__((miml(init)))',
            r'-DMIML_FINAL=__attribute__((miml(final)))',
            r'-DMIML_SENDER=__attribute__((miml(sender)))',
            r'-DMIML_RECEIVER=__attribute__((miml(receiver)))'
        ]

    def dump(self):
        pass

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
                    i = 0
                    for arg in func['args']:
                        if len(arg) == 1: #FIXME: don't stomp on already existing args
                            arg.append('_arg'+str(i))
                            i += 1
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
    def __init__(self, filename=''):
        self.filename = filename
        self.output = []

    def dump(self):
        if self.filename:
            with open(self.filename, 'w') as f:
                f.write('\n'.join(self.output))

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

class CTemplate(Template):
    delimiter='//'

class Codefile:
    def __init__(self, filename=''):
        self.filename = filename

    def dump(self):
        if self.filename:
            with open(self.filename, 'w') as f:
                f.write(self.output)

    def handle(self, tree):
        with open(path.join(tree['framework'],'elderberry/evutils.c')) as f:
            template = f.read(-1)

        headers = ''
        for header in tree['headers']:
            headers += '#include "{}"\n'.format(header)

        initfinal = ''
        for source in tree['modules'].values():
            if 'init' in source:
                initfinal += '\t{}(argc, argv, loop);\n'.format(source['init'])
            if "final" in source:
                initfinal += '\tatexit({});\n'.format(source['final'])

        wiring = ''
        for sender, receivers in tree['messages'].items():
            wiring += self.messages(tree, sender, receivers)

        subs = {'headers':headers, 'initfinal':initfinal, 'wiring':wiring}
        self.output = CTemplate(template).substitute(subs)

    def messages(self, tree, sender, receivers):
        text = ''
        src, func = sender.split('.')
        args = []
        params = []

        for parameter in tree['modules'][src]['sender'][func]: # for each param in caller
            args.append(parameter[0] + " " + parameter[1])
            params.append(parameter[1])

        text += 'void '+func+'('+', '.join(args)+') {\n'
        for receiver in receivers:
            rsrc, rfunc = receiver.split('.')
            text +='\t{}({});\n'.format(rfunc, ', '.join(params))

        text += ("}\n")
        return text

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
        self.include.append('')

        output={}
        for name, flag in modeflags.items():
            if flag:
                output[name] = self.modenames.get(name, '')
            else:
                output[name] = ''

        self.handlers = [Expand(),
                         Makefile(output.get('make', '')),
                         Codefile(output.get('code', ''))
                        ]

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
        self.master['codename'] = self.modenames.get('code', '')
        self.master['framework'] = self.framework
        self.master['include'] = self.include
        for handler in self.handlers:
            handler.handle(self.master)
            handler.dump()
