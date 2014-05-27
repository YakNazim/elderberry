#!/usr/bin/python

#     Assumptions:
#         - variable names not defined are replaced by ARG# variable name

import sys, re, os
import argparse
import yaml
import pycparser
from pycparser import c_generator, c_ast
import pycparserext
from pycparserext.ext_c_parser import GnuCParser, AttributeSpecifier
from pycparserext.ext_c_generator import GnuCGenerator

def writemiml(outputfile, output):
    try:
        with open(outputfile, 'w') as fout:
            yaml.dump(output, fout, explicit_start=True)
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

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('header', help='C header to convert to a MIML module')
    argparser.add_argument('cpp', help='Flags to pass to the C preprocessor')
    args = argparser.parse_args()
    if not args.header.endswith('.h'):
        print("Error: Input file not a .h file.")
        sys.exit(-1)

    cpp_args = args.cpp.split() + [r'-DMIML_INIT=__attribute__((miml(init)))',
                r'-DMIML_FINAL=__attribute__((miml(final)))',
                r'-DMIML_SENDER=__attribute__((miml(sender)))',
                r'-DMIML_RECEIVER=__attribute__((miml(receiver)))'
               ]

    ast = pycparser.parse_file(args.header, use_cpp=True, cpp_args=cpp_args, parser=GnuCParser())
    dv = MimlCollector()
    dv.visit(ast)

    # TODO: warn if return isn't right for the type

    basename = os.path.basename(args.header)[:-2]  # strip .h, leading path
    header = basename + '.h'
    objfile = basename + '.o'
    outputfile = basename + '.miml'

    output = {'include': header, 'object': objfile, 'senders': {}, 'receivers': {}}
    for func in dv.miml_funcs:
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

    writemiml(outputfile, output)

