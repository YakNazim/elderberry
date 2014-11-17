def plugin():
    return Makefile

class Makefile:
    def __init__(self, filename=''):
        self.filename = filename
        self.output = []

    def dump(self):
        if self.filename:
            with open(self.filename, 'w') as f:
                f.write('\n'.join(self.output))

    def rule(self, target, deps, action):
        self.output.append('{}: {}'.format(target, deps))
        if action:
            self.output.append('\t{}'.format(action))
        self.output.append('')

    def handle(self, tree):
        self.output.append('CPPFLAGS= -DMIML_INIT= -DMIML_FINAL= -DMIML_SENDER= -DMIML_RECEIVER=')
        for include in tree['include']:
            if include:
                self.output.append('CFLAGS+=-I{}'.format(include))
        self.output.append('LDLIBS=-lev')


        for source in tree['modules'].values():
            self.output.append('OBJECTS += ' + source['path'] + '/' + source['object'])
        self.output.append('')

        binary = tree['codename'].split('.')[0]

        self.rule('all', binary, '')
        self.rule(binary, '$(OBJECTS)', '')

        headers = []
        for module in tree['modules'].values():
            headers.append(module['fullpath'])
        headers = ' '.join(headers)
        action = '{}/codeGen.py {}'.format(tree['framework'], tree['mainmiml'])
        self.rule(tree['codename'], tree['mainmiml'] + ' ' + headers, action)


