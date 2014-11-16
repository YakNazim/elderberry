import yaml
from os import path
import pycparser
from pycparser import c_generator, c_ast
import pycparserext
from pycparserext.ext_c_parser import GnuCParser, AttributeSpecifier
from pycparserext.ext_c_generator import GnuCGenerator

def plugin():
    return Expand

class MimlCollector(c_ast.NodeVisitor):
    def __init__(self):
        self.miml_funcs=[]

    def get_args(self, paramlist):
        args = []
        for node in paramlist.params:
            pointers = []
            while isinstance(node.type, c_ast.PtrDecl) or isinstance(node.type, c_ast.ArrayDecl):
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

