#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
test
----------------------------------

Tests for core framework
'''

import unittest
from elderberry import codegen
import yaml

class TestSanity(unittest.TestCase):
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

    def test_missingmiml(self):
        p = codegen.Parser('tests/data/empty.conf')
        with self.assertRaises(IOError):
            p.parse('tests/data/missing.miml')

    def test_brokenmiml(self):
        p = codegen.Parser('tests/data/empty.conf')
        with self.assertRaises(yaml.YAMLError):
            p.parse('tests/data/broken.miml')


if __name__ == '__main__':
    unittest.main()
