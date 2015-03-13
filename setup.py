# -*- coding: utf-8 -*-
"""
This module contains the tool of pmr2.recipe.opencmiss
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '0.0'

long_description = (
    read('README.rst')
    + '\n' +
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('pmr2', 'recipe', 'opencmiss', 'README.rst')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.rst')
    + '\n' +
   'Download\n'
    '********\n')

entry_point = 'pmr2.recipe.opencmiss:Recipe'
entry_points = {"zc.buildout": ["default = %s" % entry_point]}

tests_require = ['zope.testing', 'zc.buildout']

setup(name='pmr2.recipe.opencmiss',
      version=version,
      description="Recipe for building OpenCMISS along with Python bindings",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        ],
      keywords='',
      author='Tommy Yu',
      author_email='tommy.yu@auckland.ac.nz',
      url='https://github.com/PMR2/pmr2.recipe.opencmiss',
      license='gpl',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['pmr2', 'pmr2.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['setuptools',
                        'zc.buildout',
                        # -*- Extra requirements: -*-
                        'zc.recipe.cmmi',
                        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite='pmr2.recipe.opencmiss.tests.test_docs.test_suite',
      entry_points=entry_points,
      )
