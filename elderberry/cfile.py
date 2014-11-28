from os import path
from string import Template

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
                initfinal += '\t{}(argc, argv);\n'.format(source['init'])
            if "final" in source:
                initfinal += '\tatexit({});\n'.format(source['final'])

        wiring = ''
        for sender, receivers in tree['messages'].items():
            wiring += self.messages(tree['modules'], sender, receivers)

        subs = {'headers':headers, 'initfinal':initfinal, 'wiring':wiring}
        self.output = CTemplate(template).substitute(subs)
        tree['codename']=self.filename

    def messages(self, modules, sender, receivers):
        text = ''
        src, func = sender.split('.')
        args = []
        params = []

        for parameter in modules[src]['sender'][func]: # for each param in caller
            args.append(parameter[0] + " " + parameter[1])
            params.append(parameter[1])

        text += 'void '+func+'('+', '.join(args)+') {\n'

        for receiver in receivers:
            rsrc, rfunc = receiver.split('.')
            text +='\t{}({});\n'.format(rfunc, ', '.join(params))

        text += ("}\n\n")
        return text

