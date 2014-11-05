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
        pass

    def test_emptyfiles(self):
        try:
            codegen.Parser('tests/data/empty.conf', {'c':False, 'm':False, 'b':False})
        except SystemExit:
            pass

if __name__ == '__main__':
    unittest.main()
