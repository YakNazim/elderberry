import string
import random
import yaml
from os import path
import pycparser
from pycparser import c_generator, c_ast
import pycparserext
from pycparserext.ext_c_parser import GnuCParser, AttributeSpecifier
from pycparserext.ext_c_generator import GnuCGenerator

def plugin():
    return Expand


class ExpandError(Exception):
    pass

class MimlCollector(c_ast.NodeVisitor):
    def __init__(self):
        self.miml_funcs=[]

    @staticmethod
    def get_arg(node):
        pointers = []
        while isinstance(node.type, (c_ast.PtrDecl, c_ast.ArrayDecl)):
            pointers.append('*')
            node = node.type
        ctype = [' '.join(node.type.type.names + pointers)]
        if node.type.declname:
            ctype.append(node.type.declname)
        return ctype

    def visit_Decl(self, node):
        for n in node.funcspec:
            if not isinstance(n, AttributeSpecifier):
                continue
            expr = n.exprlist.exprs[0]
            if not isinstance(expr, c_ast.FuncCall):
                continue
            if expr.name.name != 'miml':
                continue

            self.miml_funcs.append({
                'name': node.name,
                'file': node.coord.file,
                'miml': expr.args.exprs[0].name,
                'args': list(map(self.get_arg, node.type.args.params)),
                'type': node.type.type.type.names
            })


class Expand:
    def __init__(self, cppargs):
        try:
            self.cpp_args = cppargs.split()
        except AttributeError:
            self.cpp_args = []
        self.cpp_args += [
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

            funcions = [func for func in parsed.miml_funcs if func['file'] == fullpath]
            basename = header.split('.')[0]

            module = {}
            for func in funcions:
                if func['miml'] in ('init', 'final'):
                    self.initfinal(module, func)
                elif func['miml'] in ('sender', 'receiver'):
                    self.sendreceive(module, func)

            module['object'] = basename + '.o'
            module['file'] = header
            module['path'] = pathname
            module['fullpath'] = fullpath

            tree['modules'][basename] = module

    def findpath(self, filename):
        for pathname in self.includes:
            fullpath = path.join(pathname, filename)
            if path.exists(fullpath):
                return pathname
        else:
            raise IOError("Could not find header file: " + filename)

    def initfinal(self, module, func):
        # TODO: warn if init arg types are not right. Once I figure out what they are.
        if func['type'] != ['void']:
            raise ExpandError('Miml {} {} has incorrect return type ({})'.format(func['miml'], func['name'], func['type']))
        if func['miml'] == 'final' and list(func['args']) != [['void']]:
            raise ExpandError('Miml final function {} in {} has non-void arguments'.format(func['name'], func['file']))
        if func['miml'] in module:
            raise ExpandError('More than one miml {} specified for {}'.format(func['miml'], func['file']))
        module[func['miml']] = func['name']

    def sendreceive(self, module, func):
        if func['type'] != ['void']:
           raise ExpandError('Miml {} {} has incorrect return type ({})'.format(func['miml'], func['name'], func['type']))
        argnames = []
        for arg in func['args']:
            if len(arg) == 2:
                argnames.append(arg[1])

        argname = self.uniqueArgName(argnames)
        for i, arg in enumerate(func['args'], 1):
            if len(arg) == 1:
                arg.append(argname+str(i))

        module.setdefault(func['miml'], {})[func['name']] = func['args']

    @staticmethod
    def uniqueArgName(arguments):
    #Cantor's diagonalization. If our desired arg name is in the list of
    #provided arguments, then construct a unique random string not in the
    #list of arguments
        if '_arg' in arguments:
            unique = ''
            for i, arg in enumerate(arguments):
                try:
                    char = arg[i]
                except IndexError:
                    char = ''
                unique += random.choice(string.ascii_letters.replace(char, ''))
            return unique
        else:
            return '_arg'


