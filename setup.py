"""
A setuptools based setup module for tennet-py

Adapted from
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the version from the source code
with open(path.join(here, 'tennet', 'tennet.py'), encoding='utf-8') as f:
    lines = f.readlines()
    for l in lines:
        if l.startswith('__version__'):
            __version__ = l.split('"')[1]

setup(
    name='tennet-py',
    version=__version__,
    description='A python API wrapper for TenneT System & transmission data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/fboerman/tennet-py',
    author='Frank Boerman',
    author_email='frank@fboerman.nl',
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',

        'License :: OSI Approved :: MIT License',


        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],

    keywords='TenneT data api energy',


    packages=find_packages(),


    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed.
    install_requires=['requests', 'pandas', 'lxml'],

    package_data={
        'tennet-py': ['LICENSE.md', 'README.md'],
    },
)
