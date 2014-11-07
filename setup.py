#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='elderberry',
    version='1.9',
    description='Event driven code generation framework',
    long_description=open('README.md').read(),
    author='Theo Hill',
    author_email='theo0x48@gmail.com',
    url='http://psas-packet-serializer.readthedocs.org',
    packages=['elderberry'],
    package_dir={'elderberry': 'elderberry'},
    include_package_data=True,
    install_requires=[],
    scripts=[
        'codeGen.py',
    ],
    license=open('LICENSE').read(),
    zip_safe=False,
    classifiers=[
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
)
