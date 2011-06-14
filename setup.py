from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

# See: http://packages.python.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='tomato',
      version=version,
      description="Python SWF Processor (for Flash Lite 1.1)",
      long_description=read("README.rst"),
      keywords='SWF Flash Lite 1.1',
      classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2",
        "Topic :: Multimedia",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      author='Takahiro Kamatani',
      author_email='buhii314@gmail.com',
      url='https://github.com/buhii/tomato',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "msgpack-python>=0.1.8, !=015final",
        "bitarray",
        "PIL",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
