
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

        for name, module in tree['modules'].items():
            recvs = []
            try:
                for receiver in module['receiver']:
                    recvs.append('<{0}> {0}'.format(receiver))
            except KeyError:
                pass

            sends = []
            try:
                for sender in module['sender']:
                    sends.append('<{0}> {0}'.format(sender))
            except KeyError:
                pass

            record = '{{' + '|'.join(recvs) + ' }| ' + name + ' |{ ' + '|'.join(sends) + '}}'

            self.output.append('\t{} [shape=record, label="{}"];'.format(name, record))

        self.output.append('')

        for source, receivers in tree['messages'].items():
            srcmod = source.split('.')[0]
            srcfunc = source.split('.')[1]
            for receiver in receivers:
                recvmod = receiver.split('.')[0]
                recvfunc = receiver.split('.')[1]
                self.output.append('\t{}:{}:s -> {}:{}:n;'.format(srcmod, srcfunc, recvmod, recvfunc))
            self.output.append('')
        self.output.append('}')

