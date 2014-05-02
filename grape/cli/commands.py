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
import grape

from grape.grape import Project
from grape.cli.utils import *


class GrapeCommand(object):
    """\
    Base class for grape commands. A grape command implementation
    must provide a name and a description attribute.
    """
    def run(self, args):
        """Implement this to run the command"""
        pass

    def add(self, parser):
        """Implement this to add arguments"""
        pass


class InitCommand(GrapeCommand):
    """\
    Initialize a GRAPE project
    """
    name = "init"
    description = __doc__

    def run(self, args):
        path = args.path
        if path is None:
            error("No project path specified")
            return False

        project = Project(path)
        if project.exists():
            warn("Project already exists")
            return True

        folders = ''
        if args.type_folders:
            folders = 'type'
        if args.dataset_folders:
            folders = 'dataset'

        info("Initializing project ... ", newline=False)
        project.initialize(init_structure=not args.empty, folder_structure=folders)
        info(colored.green("Done"))

        if args.quality is not None or args.name is not None:
            info("Writing project configuration ... ", newline=False)
            if args.quality:
                project.config.set("quality", args.quality)
            if args.name:
                project.config.set("name", args.name)
            project.config._write_config()
            info(colored.green("Done"))

        return True

    def add(self, parser):
        parser.add_argument("path", default=os.getcwd(), nargs="?",
                            help="Path to the project folder. Defaults to current directory")
        parser.add_argument("--empty", dest="empty", default=False, action="store_true",
                            help="Do not create default folder structure")
        parser.add_argument("--by-type", dest="type_folders", default=False, action="store_true",
                            help="Organize project data folder by type")
        parser.add_argument("--by-dataset", dest="dataset_folders", default=False, action="store_true",
                            help="Organize project data folder by dataset")
        parser.add_argument("--quality", dest="quality", help="Set the default quality "
                                                              "offset for the project")
        parser.add_argument("--name", dest="name", help="Set the projects name")


class RunCommand(GrapeCommand):
    """\
    Run the GRAPE pipeline on a set of data
    """
    name = "run"
    description = __doc__

    def run(self, args):
        import jip
        from datetime import datetime, timedelta
        # jip parameters
        silent = False
        profiler = False
        force = False

        jobs = jip_prepare(args)

        if not jobs:
            return False

        if args.dry:
            from jip.cli import show_commands, show_dry
            show_dry(jobs)
            show_commands(jobs)
            return

        # all created and validated, time to run
        for exe in jip.jobs.create_executions(jobs):
            if exe.completed and not force:
                if not silent:
                    warn("Skipping " + exe.name)
            else:
                if not silent:
                    warn("Running {name:30}".format(name=exe.name))
                start = datetime.now()
                success = jip.jobs.run_job(exe.job, profiler=profiler)
                end = timedelta(seconds=(datetime.now() - start).seconds)
                if success:
                    if not silent:
                        info(exe.job.state + " [%s]" % (end))
                else:
                    if not silent:
                        error(exe.job.state)
                    sys.exit(1)
        return True

    def add(self, parser):
        parser.add_argument("datasets", default=["all"], nargs="*")
        parser.add_argument("--dry", default=False, action="store_true",
                            help="Show the pipeline graph and commands and exit")
        parser.add_argument("--force", default=False, action="store_true",
                            help="Force computation of all jobs")
        parser.add_argument("--compute-stats", default=False, action="store_true",
                            help="Compute md5 sums and size for jobs output files")
        add_default_job_configuration(parser,
                                            add_cluster_parameter=False)


class SubmitCommand(GrapeCommand):
    """\
    Submit the GRAPE pipeline on a set of data
    """
    name = "submit"
    description = __doc__

    def run(self, args):
        import jip

        force = args.force

        jobs = jip_prepare(args, submit=True)

        if not jobs:
            return False

        if args.dry:
            from jip.cli import show_commands, show_dry
            show_dry(jobs, profiles=True)
            show_commands(jobs)
            return

        if args.hold:
            #####################################################
            # Only save the jobs and let them stay on hold
            #####################################################
            jip.db.save(jobs)
            print "Jobs stored and put on hold"
        else:
            try:
                #####################################################
                # Iterate the executions and submit
                #####################################################
                for exe in jip.jobs.create_executions(jobs, save=True,
                                                      check_outputs=not force,
                                                      check_queued=not force):

                    if exe.job.state == jip.db.STATE_DONE and not force:
                        warn("Skipping %s" % exe.name)
                    else:
                        if jip.jobs.submit_job(exe.job, force=force):
                            info("Submitted %s with remote id %s" % (
                                exe.job.id, exe.job.job_id
                            ))
                return True
            except Exception as err:
                error("Error while submitting job: %s" % str(err))
                ##################################################
                # delete all submitted jobs
                ##################################################
                jip.jobs.delete(jobs, clean_logs=True)


    def add(self, parser):
        parser.add_argument("--dry", default=False, action="store_true",
                            help="Show the pipeline graph and commands and exit")
        parser.add_argument("--hold", default=False, action="store_true",
                            help="Submit and hold the jobs")
        parser.add_argument("--force", default=False, action="store_true",
                            help="Force job submission")
        parser.add_argument("--compute-stats", default=False, action="store_true",
                            help="Compute md5 sums and size for jobs output files")
        parser.add_argument("datasets", default=["all"], nargs="*")
        add_default_job_configuration(parser,
                                            add_cluster_parameter=True)


class JobsCommand(GrapeCommand):
    """\
    List and modify grape jobs
    """
    name = "jobs"
    description = __doc__

    def run(self, args):
        import jip
        project = Project.find()
        # setup jip db
        jip.db.init(project.jip_db)
        try:
            import runpy
            argv = ["jip-jobs"] + ['--expand'] if args.expand else []
            sys.argv = argv # reset options
            runpy.run_module("jip.jip_jobs", run_name="__main__")
        except ImportError as err:
            error("Import error. Here is the exception: %s" % str(err))

    def add(self, parser):
        parser.add_argument("--expand", default=False, action="store_true",
                            dest="expand", help="Do not collapse pipeline jobs")

class ConfigCommand(GrapeCommand):
    """\
    Get or set configuration information for the current project
    """
    name = "config"
    description = __doc__

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            error("No grape project found")
            return False

        if args.show:
            show_config(project.config, args.hidden, args.empty)
            return True
        if args.set:
            info = args.set
            project.config.set(info[0], info[1], absolute=args.absolute, commit=True)
            return True
        if args.remove:
            key = args.remove
            project.config.remove(key[0], commit=True)
            return True

        show_config(project, args.hidden, args.empty)
        return True

    def add(self, parser):
        parser.add_argument('--absolute-path', dest='absolute', action='store_true', default=False,
                        help='Use absolute path for files. Default: use path relative to the project folder')
        parser.add_argument('--hidden', action='store_true', default=False,
                        help='Include hidden information')
        parser.add_argument('--empty', action='store_true', default=False,
                        help='Include information with empty values')
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--show', action='store_true', default=False,
                        help='List the configuration information for a project')
        group.add_argument('--set', nargs=2, required=False, metavar=('key', 'value'),
                help='Add a key/value pair information to the project configuration file')
        group.add_argument('--remove', nargs=1, required=False, metavar=('key'),
                        help='Remove information to the project configuration file')


class ImportCommand(GrapeCommand):
    """\
    Import dataset information to the current project from an external csv/tsv
    file.
    """
    name = 'import'
    description = __doc__

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            error("No grape project found")
            return False

        compute_stats = args.compute_stats

        project.load(path=args.input, format=args.format)
        for dataset in project.index.datasets.values():
            for datafile in dataset.fastq.values():
                if os.path.dirname(datafile.path) != project.folder('data'):
                    dataset.rm_file(path=datafile.path, type='fastq')
                    project.add_dataset(os.path.dirname(datafile.path), dataset.id, datafile.path, datafile.path, compute_stats=compute_stats, update=True)
        project.save()

        if project.index.format and not os.path.exists(project.formatfile):
            import json
            json.dump(project.index.format, open(project.formatfile, 'w+'))

    def add(self, parser):
        parser.add_argument('input', nargs='?', type=argparse.FileType('r'), const=sys.stdin, default=sys.stdin,
                            metavar='<input_file>', help="path to the metadata file")
        parser.add_argument('-f', '--format', dest='format', default='', metavar='<format_string>', help='Format string')
        parser.add_argument("--compute-stats", default=False, dest='compute_stats', action='store_true',
                            help="Compute statistics for fastq files.")


class ExportCommand(GrapeCommand):
    """\
    Export dataset information to index file.
    """
    name = 'export'
    description = __doc__

    def run(self, args):
        project = Project.find()

        project.load()

        if not project or not project.exists():
            error("No grape project found")
            return False
        if args.output:
            signal.signal(signal.SIGPIPE, signal.SIG_DFL)
            out = args.output
            project.export(out)
            return True


    def add(self, parser):
        parser.add_argument('-o', '--output', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                            metavar='<output_file>', help='Export the project index to a standalone index format')
        parser.add_argument('-f', '--format', dest='format', default='', metavar='<format_string>', help='Format string')


class ListToolsCommand(GrapeCommand):
    """\
    List tools and pipeline configuration options
    """
    name = 'tools'
    description = __doc__

    def run(self, args):
        import jip
        from jip.cli import render_table

        print "GRAPE implemented tools"
        print "-----------------------"
        # print ""
        rows = []
        jip.scanner.scan_modules()
        for name, cls in jip.scanner.registry.iteritems():
            if name in ['bash', 'cleanup']:
                continue
            c_help = cls.help()
            description = "-"
            if c_help is not None:
                description = c_help.split("\n")[0]
            if len(description) > 60:
                description = "%s ..." % description[:46]
            rows.append((name, description))
        print render_table(["Tool", "Description"], rows)

    def add(self, parser):
        parser.add_argument('--show-config', dest='show_config', default=False, action="store_true", help="show the possible job configuration options for running the tools on a cluster")
        parser.add_argument('-c', '--create', dest='create', default=False, action="store_true", help="create a global jobs.json file with the default job configuration for all tools")
        parser.add_argument('-f', '--force', dest='force', default=False, action="store_true", help="force overwriting the existing global configuration")


class ListDataCommand(GrapeCommand):
    """\
    List project's dataset
    """
    name = "list"
    description = __doc__

    def run(self, args):
        (project, datasets) = get_project_and_datasets(args)
        if datasets is None:
            datasets = []
        puts(str(project))
        puts("%d datasets registered in project" % len(datasets))
        index = project.index.select(id=[dataset.id for dataset in datasets])
        data = index.export(type='json', absolute=True, map=None)
        if data:
            list_datasets(data, tags=index._alltags, sort=[project.index.format.get('id','id')], human=args.human, absolute=args.absolute)
        return True

    def add(self, parser):
        parser.add_argument('-n', '--numeric', dest='human', action='store_false', default=True, help='Output numbers in full numeric format')
        parser.add_argument('--absolute-path', dest='absolute', action='store_true', default=False, help='Use absolute path for files. Default: use path relative to the project folder')


class ScanCommand(GrapeCommand):
    """\
    Scan current project for new datasets
    """
    name = 'scan'
    description = __doc__

    def run(self, args):
        import re
        project = Project.find()
        try:
            project.load()
        except Exception:
            pass
        if not project or not project.exists():
            error("No grape project found")
            return False
        path = args.path
        if not path:
            path = project.folder('fastq')
        info("Scanning %s folder ... " % path, newline=False)
        fastqs = sorted(Project.search_fastq_files(path))
        info("%d fastq files found" % len(fastqs))
        if len(fastqs) == 0:
            return True

        info("Checking known data ... ", newline=False)
        fqts = set(fastqs)
        for name, dataset in project.index.datasets.items():
            if dataset.primary in fqts:
                fqts.remove(dataset.primary)
            if dataset.secondary in fqts:
                fqts.remove(dataset.secondary)
        fastqs = sorted(list(fqts))
        info("%d new files found" % len(fastqs))


        file_info = {}
        compute_stats = args.compute_stats
        update = args.update
        if args.quality:
            file_info["quality"] = args.quality
        if args.sex:
            file_info["sex"] = args.sex
        if args.read_type:
            file_info["read_type"] = args.read_type
        file_info["type"] = "fastq"

        # collect groups
        groups = {}
        scanned = []
        for fastq in fastqs:
            name = os.path.basename(fastq)
            match = re.match(r"^(?P<name>.*)(?P<id>\d)\.(fastq|fq)(\.gz)?$", name)
            if match is not None:
                try:
                    #matched_id = int(match.group("id"))
                    matched_name = match.group("name")
                    data = groups.get(matched_name, [])
                    data.append(fastq)
                    groups[matched_name] = data
                    scanned.append(fastq)
                except Exception:
                    pass

        # add all groups
        d_id = args.id
        counter = 1
        add_counter = len(groups) + (len(scanned) - len(fastqs)) > 1
        for name, files in groups.items():
            if len(files) > 2 or len(files) == 1:
                # ignore those ones and
                # add them as single entries
                for datafile in files:
                    scanned.remove(datafile)
                continue
            # try to build the id from specified id + counter or just the file
            # name
            ds_id = d_id
            if ds_id is None:
                ds_id = name
                if ds_id[-1] in ["-", ".", "_"]:
                    ds_id = ds_id[:-1]
            elif add_counter:
                ds_id = "%s_%d" % (ds_id, counter)
                counter += 1
            for datafile in files:
                project.add_dataset(path, ds_id, datafile, file_info, compute_stats=compute_stats, update=update)
        # add the singletons, everything that is not in scanned
        for datafile in set(fastqs).difference(set(scanned)):
            ds_id = id
            if ds_id is None:
                ds_id = os.path.basename(datafile)
            project.add_dataset(path, ds_id, datafile, file_info, compute_stats=compute_stats, update=update)

        project.save()

    def add(self, parser):
        parser.add_argument("path", default=None, nargs="?",
                            help="Path to folder containg the fastq files.")
        parser.add_argument("--compute-stats", default=False, dest='compute_stats', action='store_true',
                            help="Compute statistics for fastq files.")
        parser.add_argument('--sex', dest='sex', metavar='<sex>', help="Sex value assigned to new datasets")
        parser.add_argument('--id', dest='id', metavar='<id>', help="Experiment id assigned to new datasets. NOTE that a counter value is appended if more than one new dataset is found")
        parser.add_argument("--update", default=False, dest='update', action='store_true', help="Update existing index entries.")
        parser.add_argument('--absolute-path', dest='absolute', action='store_true', default=False, help='Use absolute path for files. Default: use path relative to the project folder')
        add_default_job_configuration(parser, add_cluster_parameter=False, add_pipeline_parameter=False)


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

    from grape import __version__
    import logging

    parser = argparse.ArgumentParser(prog="grape")
    parser.add_argument('--loglevel', dest='loglevel', default="WARN",
                        help='Sets the logging level')
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (__version__))

    # add commands
    command_parsers = parser.add_subparsers()
    _add_command(InitCommand(), command_parsers)
    _add_command(RunCommand(), command_parsers)
    _add_command(ListDataCommand(), command_parsers)
    _add_command(ScanCommand(), command_parsers)
    _add_command(SubmitCommand(), command_parsers)
    _add_command(ConfigCommand(), command_parsers)
    _add_command(JobsCommand(), command_parsers)
    _add_command(ImportCommand(), command_parsers)
    _add_command(ListToolsCommand(), command_parsers)
    _add_command(ExportCommand(), command_parsers)

    args = parser.parse_args()

    # setup logging
    log_level = getattr(logging, args.loglevel.upper(), None)
    grape.setup_logging(default_level=log_level)

    try:
        if not args.func(args):
            sys.exit(1)
    except KeyboardInterrupt:
        pass
    except CommandError, cerr:
        error(str(cerr))
        sys.exit(1)
    except ValueError, err:
        if str(err).startswith("GRAPE_HOME not defined."):
            error("GRAPE_HOME not found. Please make sure that the"
                      " GRAPE_HOME evironment variable is set and points"
                      " to the grape buildout directory!")
            sys.exit(1)
        else:
            raise err


def buildout():
    """The grape buildout"""
    from grape.grape import GrapeError
    from grape.buildout import Buildout
    from grape import __version__

    import logging
    grape.setup_logging()

    # tweak to control zc.buildout logger
    log = grape.get_logger('zc.buildout', 'WARN')

    parser = argparse.ArgumentParser(prog="grape-buildout")
    parser.add_argument('-c', '--config-file', dest='buildout_config',
                        default=None, help="The buildout config file")
    parser.add_argument('-d', '--buildout-dir', dest='buildout_dir',
                        default=None, help="The grape buildout directory")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (__version__))

    args = parser.parse_args()

    default_config = os.path.join(os.getcwd(), 'grape-buildout.conf')
    buildout_conf = default_config
    if args.buildout_config:
        buildout_conf = args.buildout_config

    if not buildout_conf:
        error('Please specify a configuration file')
        sys.exit(1)

    if not os.path.exists(buildout_conf):
        error('The configuration file %r does not exists', buildout_conf)
        sys.exit(1)

    grape_home = os.getenv("GRAPE_HOME", None)
    if args.buildout_dir:
        grape_home = args.buildout_dir
        log.warning("Install to %r from command line", grape_home)
    if not grape_home:
        grape_home = os.path.join(os.getenv("HOME"), ".grape", "pipeline")
        log.warning("Install to default location: %r", grape_home)
    if not os.path.exists(grape_home):
        log.info("Creating grape home folder: %r", grape_home)
        os.mkdir(grape_home)

    # get json files with Grape config
    # grape_config = [ os.path.join(os.path.dirname(__file__),f) for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".json") ]
    try:
        grape_buildout = Buildout(args.buildout_config, [('buildout', 'directory', grape_home)])
        grape_buildout.install([])

        conf_dir = os.path.join(grape_home, "conf")
        try:
            os.makedirs(conf_dir)
        except Exception:
            pass
        print "GRAPE_HOME=%s; export GRAPE_HOME;" % grape_home
        #for f in grape_config:
        #    shutil.copy(f, conf_dir)

    except GrapeError as err:
        error('Buildout error - %s', str(err))
        sys.exit(1)
