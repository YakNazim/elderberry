#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
test
----------------------------------

Tests for all parts
'''

import unittest
from elderberry import codegen
import yaml

class TestCodeGen(unittest.TestCase):
    def setUp(self):
        pass

    def test_emptyfiles(self):
        codegen.Parser('tests/data/empty.conf')

    def test_av3config(self):
        codegen.Parser('tests/data/cg.conf')

    def test_av3(self):
        p = codegen.Parser('tests/data/cg.conf')
        p.parse('tests/data/main.miml')


class TestBrokenFiles(unittest.TestCase):

    def test_missingconf(self):
        with self.assertRaises(IOError):
            codegen.Parser('tests/data/missing.conf')

    def test_brokenconf(self):
        with self.assertRaises(yaml.YAMLError):
            codegen.Parser('tests/data/broken.conf')

class TestExpander(unittest.TestCase):
    pass

if __name__ == '__main__':
    unittest.main()
