from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup
import grape

setup(
    name='Grape',
    version=grape.__version__,
    description='The Grape RNASeq pipeline version 2',
    author='Emilio Palumbo, Thasso Griebel',
    url='https://grape-pipeline.org/',
    license="GNU General Public License (GPL)",
    long_description='''Grape 2.0 provides an extensive pipeline for RNASeq
analysys.
''',
    platforms=['lx64'],
    packages=['grape', 'grape.cli', 'grape.jobs'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    install_requires=["argparse", "zc.buildout"],
    entry_points={
        'console_scripts': [
            'grape = grape.commands:main',
            'grape-buildout = grape.commands:buildout'
        ],
        'zc.buildout': [
            'install_module = grape.install_module:Recipe'
        ]
    },
)
