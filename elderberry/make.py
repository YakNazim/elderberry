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

        self.output.append('')
        binary = tree['codename'].split('.')[0]
        self.output.append('{}: $(OBJECTS)'.format(binary))
        self.output.append('')
        self.output.append('all: {}'.format(binary))


