#!/usr/bin/env python

PROJECT = 'higgsdemo'

# Change docs/sphinx/conf.py too!
VERSION = '0.1.0'

from setuptools import setup, find_packages

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='Higgs Demo',
    long_description=long_description,

    author='',
    author_email='',

    url='https://github.com/cernops/higgsdemo',
    download_url='https://github.com/cernops/higgsdemo/tarball/master',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=[
        'boto3',
        'cliff',
        'joblib',
        #'jupyterlab',
        'kubernetes', 
        'matplotlib',
        'numpy',
        'parse',
        'plotutils',
        'requests'
    ],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'higgsdemo = higgsdemo.main:main'
        ],
        'higgs.demo': [
            'cleanup = higgsdemo.cmd:Cleanup',
            'notebook = higgsdemo.cmd:Notebook',
            'prepare = higgsdemo.cmd:Prepare',
            'submit = higgsdemo.cmd:Submit',
            'watch = higgsdemo.cmd:Watch',
        ],
    },

    zip_safe=False,
)
