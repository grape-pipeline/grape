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
import time
import datetime
import logging
logging.basicConfig()

import grape
from grape.buildout import Buildout
from grape import Grape, Project, GrapeError
import grape.cli as cli
import grape.pipelines


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
            cli.error("No project path specified")
            return False

        project = Project(path)
        if project.exists():
            cli.warn("Project already exists")
            return True

        cli.info("Initializing project ... ", newline=False)
        project.initialize()
        cli.info(cli.green("Done"))
        return True

    def add(self, parser):
        parser.add_argument("path", default=os.getcwd(), nargs="?")


class RunCommand(GrapeCommand):
    name = "run"
    description = """Run the pipeline on a set of data"""

    def run(self, args):
        datasets = args.datasets
        if datasets is None:
            cli.error("No datasets specified!")
            return False

        project = Project.find()
        if project is None or not project.exists():
            cli.error("No grape project found!")
            return False

        # get default paramters
        pipelines = []
        index = project.get_indices()[0]
        annotation = project.get_annotations()[0]
        threads = args.threads

        if datasets == "all":
            datasets = project.get_datasets()

        # create default pipeline
        for d in datasets:
            pipeline = grape.pipelines.default_pipeline(d, index, annotation)
            # validate the pipeline
            if not cli.pipeline_utils.prepare_pipeline(project, pipeline):
                return False
            pipelines.append(pipeline)
            # update threads and verbose levels
            for step in pipeline.tools.values():
                step.job.threads = threads
                step.job.verbose = args.verbose

        # all created and validated, time to run
        for pipeline in pipelines:
            cli.info("Starting pipeline run: %s" % pipeline)

            steps = pipeline.get_sorted_tools()
            for i, step in enumerate(steps):

                skip = step.is_done()
                state = "Running"
                if skip:
                    state = cli.yellow("Skipped")

                s = "({0:3d}/{1}) | {2} {3:20}".format(i + 1,
                                                       len(steps),
                                                       state, step)
                cli.info(s, newline=skip)
                if not skip:
                    start_time = time.time()
                    try:
                        step.run()
                    except KeyboardInterrupt:
                        step.cleanup(failed=True)
                        cli.info(" : " + cli.red("CANCELED"))
                        return False
                    end = datetime.timedelta(seconds=int(time.time() -
                                                         start_time))
                    cli.info(" : " + cli.green("DONE") + " [%s]" % (end))
        return True

    def add(self, parser):
        parser.add_argument("datasets", default="all", nargs="*")
        parser.add_argument("-t", "--threads", default=1, dest="threads",
                            help="Number of maxium threads per step")
        parser.add_argument("--verbose", default=False, action="store_true",
                            dest="verbose")


class SubmitCommand(GrapeCommand):
    name = "submit"
    description = """Submit the pipeline on a set of data"""

    def run(self, args):
        datasets = args.datasets
        if datasets is None:
            print >> sys.stderr, "You have to specify what to submit!"

        project = Project.find()
        if project is None or not project.exists():
            print >> sys.stderr, "No grape project found!"
        else:
            if datasets == "all":
                # run on all datasets
                Grape().submit(project, args=args)

    def add(self, parser):
        parser.add_argument("datasets", default="all", nargs="*")
        parser.add_argument("-t", "--threads", default=1, dest="threads",
                            help="Number of maxium threads per step")


class ConfigCommand(GrapeCommand):
    name = "config"
    description = """Get or set configuration information fr the current project"""

    def run(self, args):
        project = Project.find()
        if project is None or not project.exists():
            print >> sys.stderr, "No grape project found!"
        else:
            if args.show:
                # print configuration
                print project.config.get_printable()
            if args.add:
                info = args.add
                project.config.set(info[0],info[1],commit=True)
            if args.remove:
                key = args.remove
                project.config.remove(key[0], commit=True)



    def add(self, parser):
        parser.add_argument('--show', action='store_true', default=False,
                        help='List all the configuration information for a project')
        parser.add_argument('--add', nargs=2, required=False, metavar=('key', 'value'),
                help='Add a key/value pair information to the project configuration file')
        parser.add_argument('--remove', nargs=1, required=False, metavar=('key'),
                        help='Remove information to the project configuration file')


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
    _add_command(ConfigCommand(), command_parsers)

    args = parser.parse_args()
    try:
        if not args.func(args):
            sys.exit(1)
    except KeyboardInterrupt:
        pass


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
        logger.error('Buildout error - %r', str(e))

