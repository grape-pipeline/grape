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


from . import cli
from . import grapeindex as index
from . import utils as grapeutils
from .grape import Grape, Project, GrapeError
from .cli import utils


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

        folders = ''
        if args.type_folders:
            folders = 'type'
        if args.dataset_folders:
            folders = 'dataset'

        cli.info("Initializing project ... ", newline=False)
        project.initialize(init_structure=not args.empty, folder_structure=folders)
        cli.info(cli.green("Done"))

        if args.quality is not None or args.name is not None:
            cli.info("Writing project configuration ... ", newline=False)
            if args.quality:
                project.config.set("quality", args.quality)
            if args.name:
                project.config.set("name", args.name)
            project.config._write_config()
            cli.info(cli.green("Done"))

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
    name = "run"
    description = """Run the pipeline on a set of data"""

    def run(self, args):
        import tools
        import jip
        from datetime import datetime, timedelta
        # jip parameters
        silent = False
        profiler = False
        force = False

        jobs = utils.jip_prepare(args)

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
                    cli.warn("Skipping " + exe.name)
            else:
                if not silent:
                    cli.warn("Running {name:30}".format(name=exe.name))
                start = datetime.now()
                success = jip.jobs.run_job(exe.job, profiler=profiler)
                end = timedelta(seconds=(datetime.now() - start).seconds)
                if success:
                    if not silent:
                        cli.info(exe.job.state + " [%s]" % (end))
                else:
                    if not silent:
                        cli.error(exe.job.state)
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
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=False)


class SubmitCommand(GrapeCommand):
    name = "submit"
    description = """Submit the pipeline on a set of data"""

    def run(self, args):
        import time
        import tools
        import jip
        from datetime import datetime, timedelta

        force = args.force

        jobs = utils.jip_prepare(args, submit=True)

        if not jobs:
            return False

        if args.dry:
            from jip.cli import show_commands, show_dry
            show_dry(jobs)
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
                        cli.warn("Skipping %s" % exe.name)
                    else:
                        if jip.jobs.submit_job(exe.job, force=force):
                            cli.info("Submitted %s with remote id %s" % (
                                exe.job.id, exe.job.job_id
                            ))
                return True
            except Exception as err:
                cli.error("Error while submitting job: %s" % str(err))
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
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=True)


class JobsCommand(GrapeCommand):
    name = "jobs"
    description = """List and modify grape jobs"""

    def run(self, args):
        import jip
        project, datasets = utils.get_project_and_datasets(args)
        # setup jip db
        jip.db.init(project.jip_db)
        try:
            import runpy
            argv = ["jip-jobs"] + ['--expand'] if args.expand else []
            sys.argv = argv # reset options
            runpy.run_module("jip.cli.jip_jobs", run_name="__main__")
        except ImportError:
            cli.error("Import error. Here is the exception:",
                      exc_info=True)

    def add(self, parser):
        parser.add_argument("--expand", default=False, action="store_true",
                            dest="expand", help="Do not collapse pipeline jobs")

class ConfigCommand(GrapeCommand):
    name = "config"
    description = """Get or set configuration information for the current project"""

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            cli.error("No grape project found")
            return False

        if args.show:
            self._show_config(project.config)
            return True
        if args.set:
            info = args.set
            project.config.set(info[0],info[1], absolute=args.absolute, commit=True)
            return True
        if args.remove:
            key = args.remove
            project.config.remove(key[0], commit=True)
            return True

        self._show_config(project, args.hidden, args.empty)
        return True

    def _show_config(self, project, show_hidden, show_empty):
        from clint.textui import indent
        # print configuration
        values = project.config.get_values(exclude=['name'], show_hidden=show_hidden, show_empty=show_empty)

        if values:
            max_keys = max([len(x[0]) for x in values]) + 1
            max_values = max([len(x[1]) for x in values]) + 1

            header = str(project)
            line = '-' * max(len(header), max_keys+max_values)

            #cli.info(line)
            cli.info(header)
            cli.info(cli.columns(['='*(max_keys-1),max_keys],['='*(max_values-1),max_values]))
            for k,v in values:
                k = cli.green(k)
                cli.info(cli.columns([k,max_keys],[v,max_values]))
            cli.info(cli.columns(['='*(max_keys-1),max_keys],['='*(max_values-1),max_values]))
            #cli.info(line)



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
    name = 'import'
    description = """Import dataset information to the current project from an external csv/tsv file."""

    def run(self, args):
        project = Project.find()
        if not project or not project.exists():
            cli.error("No grape project found")
            return False

        compute_stats=args.compute_stats

        project.load(path=args.input,format=args.format)
        for d in project.index.datasets.values():
            for file in d.fastq.values():
                if os.path.dirname(file.path) != project.folder('data'):
                    d.rm_file(path=file.path, type='fastq')
                    project.add_dataset(os.path.dirname(file.path), d.id, file.path, file, compute_stats=compute_stats, update=True)
        project.save()

        if project.index.format and not os.path.exists(project.formatfile):
            import json
            json.dump(project.index.format, open(project.formatfile,'w+'))

    def add(self, parser):
        parser.add_argument('input', nargs='?', type=argparse.FileType('r'), const=sys.stdin, default=sys.stdin,
                            metavar='<input_file>', help="path to the metadata file")
        parser.add_argument('-f', '--format', dest='format', default='', metavar='<format_string>', help='Format string')
        parser.add_argument("--compute-stats", default=False, dest='compute_stats', action='store_true',
                            help="Compute statistics for fastq files.")


class ExportCommand(GrapeCommand):
    name = 'export'
    description = """Export dataset information to index files """

    def run(self, args):
        project = Project.find()

        project.load()

        if not project or not project.exists():
            cli.error("No grape project found")
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
    name = 'tools'
    description = """List tools and pipeline configuration options"""

    def run(self, args):
        import jip
        from jip.cli import render_table

        print "GRAPE implemented tools"
        print "-----------------------"
        # print ""
        rows = []
        jip.scanner.scan_modules()
        for name, cls in jip.scanner.registry.iteritems():
            if name in ['bash','cleanup']:
                continue
            help = cls.help()
            description = "-"
            if help is not None:
                description = help.split("\n")[0]
            if len(description) > 60:
                description = "%s ..." % description[:46]
            rows.append((name, description))
        print render_table(["Tool", "Description"], rows)

    def add(self, parser):
        parser.add_argument('--show-config', dest='show_config', default=False, action="store_true", help="show the possible job configuration options for running the tools on a cluster")
        parser.add_argument('-c','--create', dest='create', default=False, action="store_true", help="create a global jobs.json file with the default job configuration for all tools")
        parser.add_argument('-f','--force', dest='force', default=False, action="store_true", help="force overwriting the existing global configuration")


class ListDataCommand(GrapeCommand):
    name = "list"
    description = """List project's datasets"""

    def run(self, args):
        (project, datasets) = utils.get_project_and_datasets(args)
        if datasets is None:
            datasets = []
        cli.puts(str(project))
        cli.puts("%d datasets registered in project" % len(datasets))
        index = project.index.select(id=[d.id for d in datasets])
        data = index.export(type='json',absolute=True, map=None)
        if data:
            self._list(data,tags=index._alltags,sort=[project.index.format.get('id','id')], human=args.human, absolute=args.absolute)
        return True

    def _list(self, data, tags=None,sort=None, human=False, absolute=True):
        from clint.textui import indent
        import json

        if tags:
            header = tags
        else:
            d = json.loads(data[0])
            header = d.keys()
        if sort:
            header = sort + [ k for k in header if k not in sort ]

        max_keys = [len(x)+1 for x in header]
        max_values = []
        len_values = []
        out=[]
        for v in data:
            v = json.loads(v)
            if 'path' in header and not absolute:
                v['path'] = os.path.join(os.path.basename(os.path.dirname(v['path'])),os.path.basename(v['path']))
            values = [ v.get(k,'-') for k in header ]
            if human:
                def isnum(x):
                    try:
                        float(x)
                        return True
                    except:
                        return False

                values = [grapeutils.human_fmt(float(v),header[1]=='size') if isnum(v) else v for i,v in enumerate(values)]
            out.append(values)
            len_values.append([len(x)+1 for x in values])
        max_values = [ max(t) for t in zip(*len_values) ]


        line = '-' * (sum([i if i>j else j for i,j in zip(max_keys,max_values)])+len(max_keys)-2)

        #cli.info(line)
        cli.info(cli.columns(*[[(max(max_keys[i],max_values[i])-1)*"=",max(max_keys[i],max_values[i])] for i,o in enumerate(header)]))
        cli.info(cli.green(cli.columns(*[[o,max(max_keys[i],max_values[i])] for i,o in enumerate(header)])))
        cli.info(cli.columns(*[[(max(max_keys[i],max_values[i])-1)*"=",max(max_keys[i],max_values[i])] for i,o in enumerate(header)]))
        #cli.info(line)
        for l in out:
            cli.info(cli.columns(*[[o, max(max_keys[i],max_values[i])] for i,o in enumerate(l)]))
        cli.info(cli.columns(*[[(max(max_keys[i],max_values[i])-1)*"=",max(max_keys[i],max_values[i])] for i,o in enumerate(header)]))
        #cli.info(line)


    def add(self, parser):
        parser.add_argument('-n','--numeric', dest='human', action='store_false', default=True,
                        help='Output numbers in full numeric format')
        parser.add_argument('--absolute-path', dest='absolute', action='store_true', default=False,
                        help='Use absolute path for files. Default: use path relative to the project folder')

        pass


class ScanCommand(GrapeCommand):
    name = 'scan'
    description = """Scan current project for new datasets"""

    def run(self, args):
        import re
        project = Project.find()
        try:
            project.load()
        except:
            pass
        if not project or not project.exists():
            cli.error("No grape project found")
            return False
        path = args.path
        if not path:
            path = project.folder('fastq')
        cli.info("Scanning %s folder ... " % path, newline=False)
        fastqs = sorted(Project.search_fastq_files(path))
        cli.info("%d fastq files found" % len(fastqs))
        if len(fastqs) == 0:
            return True

        cli.info("Checking known data ... ", newline=False)
        fqts = set(fastqs)
        for name, dataset in project.index.datasets.items():
            if (dataset.primary in fqts):
                fqts.remove(dataset.primary)
            if (dataset.secondary in fqts):
                fqts.remove(dataset.secondary)
        fastqs = sorted(list(fqts))
        cli.info("%d new files found" % len(fastqs))


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
            match = re.match("^(?P<name>.*)(?P<id>\d)\.(fastq|fq)(\.gz)?$", name)
            if match is not None:
                try:
                    id = int(match.group("id"))
                    nm = match.group("name")
                    d = groups.get(nm, [])
                    d.append(fastq)
                    groups[nm] = d
                    scanned.append(fastq)
                except Exception, e:
                    pass

        # add all groups
        id = args.id
        counter = 1
        add_counter = len(groups) + (len(scanned) - len(fastqs)) > 1
        for name, files in groups.items():
            if len(files) > 2 or len(files) == 1:
                # ignore those ones and
                # add them as single entries
                for file in files:
                    scanned.remove(file)
                continue
            # try to build the id from specified id + counter or just the file
            # name
            ds_id = id
            if ds_id is None:
                ds_id = name
                if ds_id[-1] in ["-", ".", "_"]:
                    ds_id = ds_id[:-1]
            elif add_counter:
                    ds_id = "%s_%d" % (ds_id, counter)
                    counter += 1
            for file in files:
                project.add_dataset(path, ds_id, file, file_info, compute_stats=compute_stats, update=update)
        # add the singletons, everything that is not in scanned
        for file in set(fastqs).difference(set(scanned)):
            ds_id = id
            if ds_id is None:
                ds_id = os.path.basename(file)
            project.add_dataset(path, ds_id, file, file_info, compute_stats=compute_stats, update=update)

        project.save()



    def add(self, parser):
        parser.add_argument("path", default=None, nargs="?",
                            help="Path to folder containg the fastq files.")
        parser.add_argument("--compute-stats", default=False, dest='compute_stats', action='store_true',
                            help="Compute statistics for fastq files.")
        parser.add_argument('--sex', dest='sex', metavar='<sex>', help="Sex value assigned to new datasets")
        parser.add_argument('--id', dest='id', metavar='<id>', help="Experiment id assigned to new datasets. "
                                                                    "NOTE that a counter value is appended if more than "
                                                                    "one new dataset is found")
        parser.add_argument("--update", default=False, dest='update', action='store_true',
                            help="Update existing index entries.")
        parser.add_argument('--absolute-path', dest='absolute', action='store_true', default=False,
                            help='Use absolute path for files. Default: use path relative to the project folder')
        utils.add_default_job_configuration(parser,
                                            add_cluster_parameter=False,
                                            add_pipeline_parameter=False)



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
    _add_command(ListDataCommand(), command_parsers)
    _add_command(ScanCommand(), command_parsers)
    _add_command(SubmitCommand(), command_parsers)
    _add_command(ConfigCommand(), command_parsers)
    _add_command(JobsCommand(), command_parsers)
    _add_command(ImportCommand(), command_parsers)
    _add_command(ListToolsCommand(), command_parsers)
    _add_command(ExportCommand(), command_parsers)

    args = parser.parse_args()
    try:
        if not args.func(args):
            sys.exit(1)
    except KeyboardInterrupt:
        pass
    except cli.utils.CommandError, ce:
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
    import shutil
    from .buildout import Buildout
    from . import __version__

    import logging
    logging.root.handlers = []

    parser = argparse.ArgumentParser(prog="grape-buildout")
    parser.add_argument('-v', '--version', action='version',
                        version='grape %s' % (__version__))

    args = parser.parse_args()

    buildout_conf = os.path.join(os.path.dirname(__file__), 'buildout.conf')

    # get json files with Grape config
    # grape_config = [ os.path.join(os.path.dirname(__file__),f) for f in os.listdir(os.path.dirname(__file__)) if f.endswith(".json") ]
    try:
        buildout = Buildout(buildout_conf, [('buildout','directory', os.getenv("GRAPE_HOME"))])
        buildout.install([])

        conf_dir = os.path.join(os.getenv("GRAPE_HOME"),"conf")
        try:
            os.makedirs(conf_dir)
        except:
            pass
        #for f in grape_config:
        #    shutil.copy(f, conf_dir)


    except GrapeError as e:
        cli.error('Buildout error - %s', str(e))
        sys.exit(1)

