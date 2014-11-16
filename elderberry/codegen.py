import yaml
import logging
import sys
from os import path
import importlib

class Parser:
    def __init__(self, config):
        try:
            with open(config, 'r') as conf:
                config = yaml.load(conf)
        except IOError as e:
            logging.error("Opening config: " + str(e))
            raise
        except yaml.YAMLError as e:
            logging.error("YAML parsing error in config: " + str(e))
            raise

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
            plugin = importlib.import_module(name).plugin()
            self.handlers.append(plugin(config))

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
        self.master['framework'] = self.framework
        self.master['include'] = self.include

        for handler in self.handlers:
            handler.handle(self.master)
            handler.dump()
