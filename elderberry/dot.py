
def plugin():
    return Dot

class Dot:
    def __init__(self, filename):
        self.filename = filename
        self.output = []

    def dump(self):
        if self.filename:
            with open(self.filename, 'w') as f:
                f.write('\n'.join(self.output))

    def handle(self, tree):
        self.output.append('digraph elderberry {')
        for source, receivers in tree['messages'].items():
            srcmod = source.split('.')[0]
            for receiver in receivers:
                recvmod = receiver.split('.')[0]
                self.output.append('\t{} -> {};'.format(srcmod, recvmod))
            self.output.append('')
        self.output.append('}')

