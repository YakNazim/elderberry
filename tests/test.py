#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
test
----------------------------------

Tests for all parts
'''

import unittest
from elderberry import codegen


class TestCodeGen(unittest.TestCase):
    def setUp(self):
        print('')

#    def test_emptyfiles(self):
#        codegen.Parser('tests/data/empty.conf', {})

    def test_av3config(self):
        codegen.Parser('tests/data/cg.conf', {'code':False, 'make':False, 'header':False})

    def test_av3(self):
        p = codegen.Parser('tests/data/cg.conf', {'code':False, 'make':False, 'header':False})
        p.parse('tests/data/main.miml')


if __name__ == '__main__':
    unittest.main()
