#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
test_expand
----------------------------------

Tests for the expand plugin
'''

import unittest
from elderberry import expand

class TestExpander(unittest.TestCase):

    def setUp(self):
        self.expand = expand.Expand(None)
        self.tree = {
            'include': [''],
            'headers': [],
        }

    def test_sanity(self):
        self.expand.handle(self.tree)

    def test_missingheader(self):
        self.tree['headers'].append('tests/data/missing.h')
        with self.assertRaises(IOError):
            self.expand.handle(self.tree)


    def test_complicatedheader(self):
        self.tree['headers'].append('tests/data/complicated.h')
        self.expand.handle(self.tree)
