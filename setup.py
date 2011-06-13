from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

setup(name='tomato',
      version=version,
      description="Python SWF Processor (for Flash Lite 1.1)",
      long_description="Python SWF Processor (for Flash Lite 1.1)",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Takahiro Kamatani',
      url='https://github.com/buhii/tomato.git',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "msgpack-python",
        "bitarray",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
