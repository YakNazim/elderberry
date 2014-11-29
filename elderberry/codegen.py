import yaml
import sys
from os import path
import importlib

class Parser:
    def __init__(self, config):
        with open(config, 'r') as conf:
            config = yaml.load(conf)

        try:
            stages = config.pop('stages', [])
            self.include = config.pop('include', [])
            self.framework = config.pop('framework', '.')
        except AttributeError:
            stages = []
            self.include = []
            self.framework = '.'
        self.include.append('')
        self.handlers = []
        for stage in stages:
            name, config = stage.popitem()
            module, objectname = name.rsplit('.', 1)
            plugin = getattr(importlib.import_module(module), objectname)
            self.handlers.append(plugin(config))

    def parse(self, mainmiml):
        with open(mainmiml, 'r') as miml:
            self.master = yaml.load(miml)

        self.master['mainmiml'] = mainmiml
        self.master['framework'] = self.framework
        self.master['include'] = self.include

        for handler in self.handlers:
            handler.handle(self.master)
            handler.dump()
