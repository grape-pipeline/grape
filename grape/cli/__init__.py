#!/usr/bin/env python
"""Command line helpers"""

import sys

from clint.textui import puts, colored
from clint.textui.colored import *

from .pipeline_utils import *


def error(msg, newline=True):
    """Print an error message"""
    puts(colored.red(msg), stream=sys.stderr.write, newline=newline)
    sys.stderr.flush()


def info(msg, newline=True):
    """Print an info message"""
    puts(msg, stream=sys.stdout.write, newline=newline)
    sys.stdout.flush()


def warn(msg, newline=True):
    """Print an warning message"""
    puts(colored.yellow(msg), stream=sys.stdout.write, newline=newline)
    sys.stdout.flush()
