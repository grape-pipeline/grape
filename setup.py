from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup


setup(
    name='Grape',
    version="2.0-alpha.1",
    description='The Grape RNASeq pipeline verison 2',
    author='Emilio Palumbo, Thasso Griebel',
    url='https://grape-pipeline.org/',
    license="GNU General Public License (GPL)",
    long_description='''Grape 2.0 provides an extensive pipeline for RNASeq
analysys.
''',
    packages=['grape'],
    platforms=['lx64'],
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
    install_requires=["argparse"],
    entry_points={
        'console_scripts': [
            'grape = grape.commands:main'
        ]
    },
)
