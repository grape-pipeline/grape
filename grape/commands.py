#!/usr/bin/env python
"""Grape command line tools.

This module provides the infrastructure to add command line tools to the
grape command. In order to create a new command, create a subclass of
GrapeCommand and make sure you add a name and a description. The command
implementation can then implement the add() method to add command line
options to the given argpaser parser and the run() method that takes
the parsed command line options and executes the command.

"""
import argparse
import sys
import os
import logging

import grape
from grape.buildout import Buildout
from grape import Grape, Project, GrapeError


class GrapeCommand(object):
    """Base class for grape commands. A grape command implementation
    must provide a name and a description attribute.
    """
    def run(self, args):
        """Implement this to run the command"""
        pass

    def add(self, parser):
        """Implement this to add arguments"""
        pass


class InitCommand(GrapeCommand):
    name = "init"
    description = """Initialize a grape project"""

    def run(self, args):
        path = args.path
        if path is None:
            print >> sys.stderr, "You have to specify a path to the project"
        project = Project(path)
        if project.exists():
            print >> sys.stderr, "Project exists!"
        else:
            print >> sys.stderr, "Initializing project"
            project.initialize()
            print >> sys.stderr, "Done"

    def add(self, parser):
        parser.add_argument("path", default=os.getcwd(), nargs="?")


class RunCommand(GrapeCommand):
    name = "run"
    description = """Run the pipeline on a set of data"""

    def run(self, args):
        datasets = args.datasets
        if datasets is None:
            print >> sys.stderr, "You have to specify what to run!"

        project = Project.find()
        if project is None or not project.exists():
            print >> sys.stderr, "No grape project found!"
        else:
            if datasets == "all":
                # run on all datasets
                Grape().run(project)

    def add(self, parser):
        parser.add_argument("datasets", default="all", nargs="*")


def _add_command(command, command_parser):
    """Add a command instance to the set of command parsers

    Parameter
    ---------
    command        - the command instance
    command_parser - the argparser subparsers where this command is added
    """
    subparser = command_parser.add_parser(command.name,
                                          help=command.description)
    subparser.set_defaults(func=command.run)
    command.add(subparser)


def main():
    """The grape main method that is triggered by the `grape` command
    line tool"""
    parser = argparse.ArgumentParser(prog="grape")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (grape.__version__))

    # add commands
    command_parsers = parser.add_subparsers()
    _add_command(InitCommand(), command_parsers)
    _add_command(RunCommand(), command_parsers)

    args = parser.parse_args()
    args.func(args)


def buildout():
    """The grape buildout"""
    parser = argparse.ArgumentParser(prog="grape-buildout")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (grape.__version__))

    args = parser.parse_args()

    logger = logging.getLogger('grape')
    buildout_conf = os.path.join(os.path.dirname(__file__), 'buildout.conf')

    try:
        buildout = Buildout(buildout_conf)
        buildout.install([])
    except GrapeError as e:
        logger.error('Buildout error - %r', e)
    finally:
        buildout.cleanup()

