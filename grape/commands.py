#!/usr/bin/env python
"""Grape command line tools.

This module provides the infrastructure to add command line tools to the
grape command. In order to create a new command, create a subclass of
GrapeCommand and make sure you add a name and a description. The command
implementation can then implement the add() method to add command line
options to the given argpaser parser and the run() method that takes
the parsed command line options and executes the command.

"""


import sys
import os
import signal
import argparse

#
# import grape
#
from .grape import Grape, Project, GrapeError

from . import cli
from . import jobs
from .cli import utils
from .jobs.store import PipelineStore
from jip.tools import ToolException




class CommandError(Exception):
    """Exception raised by command line tools. This exception
    is catched in the main call and no stack trace is printed, just
    the error message"""
    pass


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

class SetupCommand(GrapeCommand):
    name = "setup"
    description = """Run the pre-processing steps needed to prepare the pipeline for the execution"""

    def run(self, args):
        import time, datetime
        # get the project and the selected datasets
        project, datasets = utils.get_project_and_datasets(args)
        pipelines = []
        grp = grape.Grape()
        pipeline = grape.pipelines.pre_pipeline(project.config)
        # update job params
        for step in pipeline.tools.values():
            grp.configure_job(step, project, None, vars(args))


        # validate the pipeline
        if not utils._prepare_pipeline(pipeline):
            raise ValueError('Cannot prepare pipeline')
        pipelines.append(pipeline)
        if not pipelines:
            raise ValueError('No pipelines found')
        if args.submit:
            cluster = Grape().get_cluster()
        # all created and validated, time to run
        for pipeline in pipelines:
            cli.info("Setting up %s" % pipeline)
            if args.submit:
                store = PipelineStore(project.path, pipeline.name)
            steps = pipeline.get_sorted_tools()
            for i, step in enumerate(steps):
                skip = step.is_done()
                state = "Running"
                if skip:
                    state = cli.yellow("Skipped")
                    jobid = ""
                if args.submit:
                    if not skip:
                        state = cli.green("Submitted")
                        step.job.name = "GRP-SET-%s" % (str(step))
                        grape.jobs.store.prepare_tool(step._tool, project.path,
                                                      pipeline.name)

                        # we need to explicitly lock the store here as the
                        # job is already on the cluster and we need to make
                        # sure the cluster jobs does not updated the entry before
                        # we actually set it
                        store.lock()
                        feature = cluster.submit(step,
                                                 step.get_configuration())
                        jobid = feature.jobid
                        store_entry = {
                            "id": jobid,
                            "stderr": feature.stderr,
                            "stdout": feature.stdout,
                            "state": jobs.STATE_QUEUED
                        }
                        store.set(str(step), store_entry)
                        store.release()

                    s = "({0:3d}/{1}) | {2} {3:20} {4}".format(i + 1,
                                                           len(steps),
                                                           state, step,
                                                           jobid)
                    cli.info(s)
                else:
                    s = "({0:3d}/{1}) | {2} {3:20}".format(i + 1,
                                                       len(steps),
                                                       state, step)
                    cli.info(s, newline=skip)
                    if not skip:
                        start_time = time.time()
                        try:
                            step.run()
                        except ToolException, err:
                            if err.termination_signal == signal.SIGINT:
                                cli.info(" : " + cli.yellow("CANCELED"))
                            else:
                                cli.info(" : " + cli.red("FAILED " + str(err.exit_value)))
                            return False
                        end = datetime.timedelta(seconds=int(time.time() - start_time))
                        cli.info(" : " + cli.green("DONE") + " [%s]" % end)
        return True

    def add(self, parser):
        parser.add_argument('--submit', action='store_true', default=False,
                            help='Run the setup steps in a HPC cluster environment - requires a working cluster configuration')
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=False)

class RunCommand(GrapeCommand):
    name = "run"
    description = """Run the pipeline on a set of data"""

    def run(self, args):
        import time, datetime
        # get the project and the selected datasets
        project, datasets = utils.get_project_and_datasets(args)
        pipelines = utils.create_pipelines(grape.pipelines.default_pipeline,
                                           project,
                                           datasets, vars(args))
        if not pipelines:
            return False

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
                    grape.index.prepare_tool(step._tool, project.path, pipeline.get_configuration(pipeline.tools[step._tool.name]))
                    start_time = time.time()
                    try:
                        step.run()
                    except ToolException, err:
                        if err.termination_signal == signal.SIGINT:
                            cli.info(" : " + cli.yellow("CANCELED"))
                        else:
                            cli.info(" : " + cli.red("FAILED " + str(err.exit_value)))
                        return False
                    end = datetime.timedelta(seconds=int(time.time() - start_time))
                    cli.info(" : " + cli.green("DONE") + " [%s]" % end)
        return True

    def add(self, parser):
        parser.add_argument("datasets", default=["all"], nargs="*")
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=False)


class JobsCommand(GrapeCommand):
    name = "jobs"
    description = """List and modify grape jobs"""

    def run(self, args):
        grp = Grape()
        cluster = grp.get_cluster()

        # list jobs
        self._list_jobs(args, cluster)

    def _get_stores(self, project, check=False, cluster=None):
        """Iterates over all project job stores and collects
        the data. If check is set to True and a cluster is
        specified, the cluster jobs are listed and the states
        are updated.
        """
        stores = []
        job_states = None
        for store in grape.jobs.store.list(project.path):
            try:
                store.lock()
                data = store.get()
                if check:
                    changed = False
                    # check job status
                    for k, v in data.items():
                        if k in ["name"]:
                            continue
                        if v.get("state", None) in [grape.jobs.STATE_QUEUED,
                                                    grape.jobs.STATE_RUNNING]:
                            if job_states is None:
                                job_states = cluster.list()
                            if v["id"] not in job_states:
                                v["state"] = grape.jobs.STATE_FAILED
                                changed = True
                    if changed:
                        store.save(data)
                stores.append(data)
            finally:
                store.release()
        return stores

    def _list_jobs(self, args, cluster):
        """List grape jobs

        :param cluster: the cluster instance
        :type cluster: jip.cluster.Cluster
        """
        project, datasets = utils.get_project_and_datasets(args)

        stores = self._get_stores(project, check=args.check, cluster=cluster)

        if args.verbose:
            self._list_verbose(stores)
            return True

        names = []
        states = []
        bars = []
        for data in stores:
            raw_states = []
            for k, v in data.items():
                if k not in ["name"]:
                    raw_states.append(v["state"])

            # print overview
            counts = {}
            def _count(k):
                counts[k] = counts.get(k, 0) + 1
            map(_count, raw_states)

            pipeline_state = cli.green(grape.jobs.STATE_DONE)
            if counts.get(grape.jobs.STATE_FAILED, 0) > 0:
                pipeline_state = cli.red(grape.jobs.STATE_FAILED)
            if counts.get(grape.jobs.STATE_RUNNING, 0) > 0:
                pipeline_state = cli.white(grape.jobs.STATE_RUNNING)
            if counts.get(grape.jobs.STATE_QUEUED, 0) > 0:
                pipeline_state = cli.yellow(grape.jobs.STATE_QUEUED)

            BAR_TEMPLATE = '[%s%s] %i/%i'
            bar = None
            count = len(raw_states)
            width = 32
            i = counts.get(grape.jobs.STATE_DONE, 0)
            x = int(width * i / count)
            bar = BAR_TEMPLATE % (
                '#' * x,
                ' ' * (width - x),
                i,
                count
            )
            names.append(data["name"])
            states.append(pipeline_state),
            bars.append(bar)

        max_names = max(map(len, names)) + 2
        max_state = max(map(len, states)) + 2
        for i, name in enumerate(names):
            cli.info(cli.columns(
                [name, max_names],
                [states[i], max_state],
                [bars[i], None]))



    def _list_verbose(self, stores):
        for data in stores:
            names = []
            states = []
            ids = []
            for k, v in data.items():
                if k not in ["name"]:
                    names.append(k)
                    ids.append(str(v.get("id", "")))
                    s = v.get("state", "")
                    if s == grape.jobs.STATE_QUEUED:
                        states.append(cli.yellow(s))
                    elif s == grape.jobs.STATE_RUNNING:
                        states.append(cli.white(s))
                    elif s == grape.jobs.STATE_DONE:
                        states.append(cli.green(s))
                    else:
                        states.append(cli.red(s))

            max_names = max(map(len, names)) + 2
            max_ids = max(map(len, ids)) + 2
            cli.info("Pipeline: " + data["name"])
            for i, name in enumerate(names):
                cli.info(cli.columns(
                    [name, max_names],
                    [ids[i], max_ids],
                    [states[i], None]))


    def add(self, parser):
        parser.add_argument("--check", default=False, action="store_true",
                            dest="check", help="Check the jobs status by "
                                               "querying the cluster")
        parser.add_argument("-v", "--verbose", default=False,
                            action="store_true",
                            dest="verbose", help="Print job details")
        pass
        #parser.add_argument("datasets", default="all", nargs="*")


class SubmitCommand(GrapeCommand):
    name = "submit"
    description = """Submit the pipeline on a set of data"""

    def run(self, args):
        # get the project and the selected datasets
        project, datasets = utils.get_project_and_datasets(args)
        pipelines = utils.create_pipelines(grape.pipelines.default_pipeline,
                                           project,
                                           datasets,
                                           vars(args))

        if not pipelines:
            return False

        # all created and validated, time to run
        grp = Grape()
        cluster = grp.get_cluster()

        for pipeline in pipelines:
            cli.info("Submitting pipeline run: %s" % pipeline)
            store = PipelineStore(project.path, pipeline.name)

            steps = pipeline.get_sorted_tools()
            for i, step in enumerate(steps):
                skip = step.is_done()
                if skip:
                    state = cli.yellow("Skipped")
                    jobid = ""
                else:
                    state = cli.green("Submitted")
                    step.job.name = "GRP-%s" % (str(step))
                    grape.index.prepare_tool(step._tool, project.path, pipeline.get_configuration(pipeline.tools[step._tool.name]))
                    grape.jobs.store.prepare_tool(step._tool, project.path,
                                                  pipeline.name)

                    # we need to explicitly lock the store here as the
                    # job is already on the cluster and we need to make
                    # sure the cluster jobs does not updated the entry before
                    # we actually set it
                    store.lock()
                    feature = cluster.submit(step,
                                             step.get_configuration())
                    jobid = feature.jobid
                    store_entry = {
                        "id": jobid,
                        "stderr": feature.stderr,
                        "stdout": feature.stdout,
                        "state": jobs.STATE_QUEUED
                    }
                    store.set(str(step), store_entry)
                    store.release()

                s = "({0:3d}/{1}) | {2} {3:20} {4}".format(i + 1,
                                                           len(steps),
                                                           state, step,
                                                           jobid)
                cli.info(s)
        return True


    def add(self, parser):
        parser.add_argument("datasets", default=["all"], nargs="*")
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=True)


class ConfigCommand(GrapeCommand):
    name = "config"
    description = """Get or set configuration information for the current project"""

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            cli.error("No grape project found")
            return False

        if args.show:
            # print configuration
            print project.config.get_printable()
            return True
        if args.set:
            info = args.set
            project.config.set(info[0],info[1],commit=True)
            return True
        if args.remove:
            key = args.remove
            project.config.remove(key[0], commit=True)
            return True

        print project.config.get_printable()
        return True

    def add(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--show', action='store_true', default=False,
                        help='List all the configuration information for a project')
        group.add_argument('--set', nargs=2, required=False, metavar=('key', 'value'),
                help='Add a key/value pair information to the project configuration file')
        group.add_argument('--remove', nargs=1, required=False, metavar=('key'),
                        help='Remove information to the project configuration file')

class ImportCommand(GrapeCommand):
    name = 'import'
    description = """Import dataset information to the current project from an external csv/tsv file."""

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            cli.error("No grape project found")
            return False

        file = args.input
        if file is sys.stdin:
            import tempfile
            t = tempfile.TemporaryFile('r+w')
            for line in file:
                t.write(line)
            t.seek(0)
            file = t

        if type == 'index':
            project.index.load(file)
        else:
            project.import_data(file, id=args.id_key, path=args.path_key)
        project.index.save()

    def add(self, parser):
        parser.add_argument('input', nargs='?', type=argparse.FileType('r'), const=sys.stdin, default=sys.stdin,
                            metavar='<input_file>', help="path to the metadata file")
        parser.add_argument('--id-key', dest='id_key', default='labExpId', metavar='<id_key>')
        parser.add_argument('--path-key', dest='path_key', default='path', metavar='<path_key>')


class ExportCommand(GrapeCommand):
    name = 'export'
    description = """Export dataset information to index files """

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            cli.error("No grape project found")
            return False
        if args.output:
            #if args.fields:
            #    cli.error("Invalid argument")
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            out = args.output
            project.index.export(out, absolute=True)
            return True


    def add(self, parser):
        parser.add_argument('-o', '--output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                            metavar='<output_file>', help='Export the project index to a standalone index format')
        #parser.add_argument('--custom-fields', dest='fields', nargs='+', help='Get a list of custom field to add to the index')

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

    from . import __version__
    parser = argparse.ArgumentParser(prog="grape")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (__version__))
    # add commands
    command_parsers = parser.add_subparsers()
    _add_command(InitCommand(), command_parsers)
    _add_command(RunCommand(), command_parsers)
    _add_command(SubmitCommand(), command_parsers)
    _add_command(ConfigCommand(), command_parsers)
    _add_command(JobsCommand(), command_parsers)
    _add_command(ImportCommand(), command_parsers)
    #_add_command(ExportCommand(), command_parsers)
    _add_command(SetupCommand(), command_parsers)

    args = parser.parse_args()
    try:
        if not args.func(args):
            sys.exit(1)
    except KeyboardInterrupt:
        pass
    except CommandError, ce:
        cli.error(str(ce))
        sys.exit(1)
    except ValueError, e:
        if str(e).startswith("GRAPE_HOME not defined."):
            cli.error("GRAPE_HOME not found. Please make sure that the"
                      " GRAPE_HOME evironment variable is set and points"
                      " to the grape buildout directory!")
            sys.exit(1)
        else:
            raise e


def buildout():
    """The grape buildout"""
    from .buildout import Buildout
    from . import __version__
    parser = argparse.ArgumentParser(prog="grape-buildout")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (__version__))

    args = parser.parse_args()

    buildout_conf = os.path.join(os.path.dirname(__file__), 'buildout.conf')

    try:
        buildout = Buildout(buildout_conf)
        buildout.install([])
    except GrapeError as e:
        cli.error('Buildout error - %r', str(e))
        sys.exit(1)

