from distribute_setup import use_setuptools
use_setuptools()
from sys import exit
from setuptools import setup
from setuptools.command.test import test as TestCommand

import grape

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['tests']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        exit(errno)

setup(
    name='grape-pipeline',
    version=grape.__version__,
    description='The Grape RNASeq pipeline version 2',
    author='Emilio Palumbo, Thasso Griebel',
    url='https://grape-pipeline.org/',
    license="GNU General Public License (GPL)",
    long_description='''Grape 2.0 provides an extensive pipeline for RNASeq
analysys.
''',
    platforms=['lx64'],
    packages=['grape', 'grape.cli'],
    package_data={'grape': ['buildout.conf']},
    tests_require=['pytest'],
    cmdclass = {'test': PyTest},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    install_requires=["argparse==1.2.1",
                      "clint==0.3.1",
                      "lockfile==0.9.1",
                      "pyjip==0.4",
                      "idxtools==0.9.1"],
    entry_points={
        'console_scripts': [
            'grape = grape.cli.commands:main',
            'grape-buildout = grape.cli.commands:buildout'
        ],
        'zc.buildout': [
            'install_module = grape.install_module:Recipe'
        ]
    },
)
