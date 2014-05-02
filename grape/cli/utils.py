"""Grape command line utilities"""

import sys
import jip
import os
from clint.textui import puts, colored, columns


class CommandError(Exception):
    """Exception raised by command line tools. This exception
    is catched in the main call and no stack trace is printed, just
    the error message"""
    pass


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


def jip_prepare(args, submit=False, project=None, datasets=[], validate=True):
    # get the project and the selected datasets
    if not project and not datasets:
        project, datasets = get_project_and_datasets(args)
    # setup jip db
    jip.db.init(project.jip_db)
    p = jip.Pipeline()

    # load profile
    profile = jip.profiles.get(name='default')
    #                           if not args.profile
    #                           else args.profile)
    profile.tool_name = 'grape'
    pro_args = {}
    pro_args['mem'] = args.max_mem
    pro_args['threads'] = args.threads
    pro_args['queue'] = args.queue
    pro_args['time'] = args.max_time
    profile.load_args(pro_args)
    #log.info("Profile: %s", profile)

    jargs = {}
    if datasets == ['setup']:
        jargs['input'] = project.config.get('genome')
        jargs['annotation'] = project.config.get('annotation')
        p.run('grape_gem_setup', **jargs)
        jobs = jip.jobs.create_jobs(p, profile=profile)
    else:
        input = []
        for d in datasets:
            fqs = d.fastq.keys()
            fqs.sort()
            input.append(fqs[0])
            if len(fqs) == 1:
                jargs['single-end'] == True
        jargs['fastq'] = input
        jargs['annotation'] = project.config.get('annotation')
        jargs['genome'] = project.config.get('genome')
        jargs['max_mismatches'] = args.max_mismatches
        jargs['max_matches'] = args.max_matches
        jargs['threads'] = args.threads
        p.run('grape_gem_rnapipeline', **jargs)
        jobs = jip.jobs.create_jobs(p, validate=validate, profile=profile)
    if submit:
        jobs = check_jobs_dependencies(jobs)
    return jobs

def check_jobs_dependencies(jobs):
    out_jobs = []
    for j in jobs:
        add_job = True
        list = []
        js = get_setup_jobs(j)
        for job in js:
            if job.name == j.name:
                add_job = False
                break
            if job.name in [o.name for o in j.dependencies]:
                j.state = jip.db.STATE_QUEUED
                for c in j.children:
                    c.state = jip.db.STATE_QUEUED
                if not job in list:
                    list += [job]
        if list:
            names = [job.name for job in list]
            old_deps = [d for d in j.dependencies if d.name not in names]
            j.dependencies = list + old_deps
        if add_job:
            out_jobs.append(j)
    return out_jobs


def get_setup_jobs(job):
    setup_jobs = []
    query = None
    if str(job._tool) == 'grape_gem_index':
        query = jip.db.query_by_files(job.tool.input.value,job.tool.output.value, and_query=True)
    if str(job._tool) == 'grape_gem_t_index':
        query = jip.db.query_by_files(job.tool.index.value, job.tool.gem.value, and_query=True)
    job_list = query.all() if query else None
    if job_list:
        s_job = job_list[0]
        if s_job.state == jip.db.STATE_FAILED:
            remove_job(s_job)
            return []
        setup_jobs = [s_job]
    for j in job.dependencies:
        setup_jobs += get_setup_jobs(j)
    return [j for j in setup_jobs if j]

def remove_job(job):
    for j in job.children:
        remove_job(j)
    jip.jobs.delete(job, clean_logs=True)
    warn('Removed job %s[%s]' % (job.name, job.id))
    return True

def get_project_and_datasets(args):
    """Get the current project and the selected datasets using the command
     line arguments.

     :raise grape.commands.CommandError: in case a error occured
     :returns (project, datasets): tuple with the project and the selected
         datasets
    """
    from grape.grape import Project
    from indexfile.index import Dataset
    import os, re

    datasets = None

    project = Project.find()
    if not project or not project.exists():
        project = Project(os.getcwd())
        project.initialize()
        datasets = prepare_from_commandline(project, args)

    if "datasets" in args and not datasets:
        datasets = args.datasets
    else:
        datasets = ["all"]

    if 'setup' in datasets:
        return (project, ['setup'])

    if datasets is None:
        raise CommandError("No datasets specified!")
    if datasets == ['all']:
        datasets = []

    datasets = project.get_datasets(id=datasets)

    return (project, datasets)

def prepare_from_commandline(project, args):
    """Prepare index and configuration for running the pipeline from commandline on a new automatically created project.

     :raise grape.commands.CommandError: in case a error occured
     :returns (project, datasets): tuple with the project and the selected
         datasets
    """
    from grape.grape import Project
    from indexfile.index import Dataset
    import os

    metadata = {'type':'fastq'}
    datasets = None

    if 'genome' in args and args.genome:
        project.config.set('genome',os.path.abspath(args.genome),
                               commit=True)
        args.genome = project.config.get('genome')
        if os.path.exists("%s.gem" % os.path.abspath(args.genome)):
            project.config.set('index',"%s.gem" % os.path.abspath(args.genome),
                                                   commit=True)
    if 'annotation' in args and args.annotation:
        project.config.set('annotation',os.path.abspath(args.annotation),
                               commit=True)
        args.annotation = project.config.get('annotation')
        for t in [('t-index','gem'),('keys','keys')]:
            if os.path.exists("%s.junctions.%s" % (os.path.abspath(args.annotation), t[1])):
                project.config.set(t[0],"%s.junctions.%s" % (os.path.abspath(args.annotation), t[1]),
                                                   commit=True, dest='annotations')
    if 'quality' in args and args.quality:
        project.config.set('quality', args.quality, commit=True)
        metadata['quality'] = args.quality

    if 'read_type' in args and args.read_type:
        metadata['readType'] = args.read_type

    if 'input' in args and args.input:
        ds = {}
        for dataset in args.input:
            if Project.find_dataset(dataset):
                name, files = Project.find_dataset(dataset)
                ds[name] = files
        for name, files in ds.items():
            if len(files) > 1 and not 'readType' in metadata:
                metadata['readType'] = '2x'
            for f in files:
                project.add_dataset(os.path.dirname(f), name, f, metadata, compute_stats=False, update=False)

        project.save(reload=True)

        datasets = project.get_datasets(id=ds.keys())

    return datasets


def add_default_job_configuration(parser, add_cluster_parameter=True, add_pipeline_parameter=True, add_dataset_parameter=True):
    """Add the default job configuration options to the given argument
    parser

    :param parser: the argument parser
    :type parser: argparse.ArgumentParser
    :param add_cluster_parameter: add additional cluster parameter
    :type add_cluster_parameter: bool
    """
    group = parser.add_argument_group("Global Runtime",
                                      "Global runtime parameter that are "
                                      "applied to all jobs")
    group.add_argument("-c", "--cpus", dest="threads",
                        help="Number of threads/cpus assigned to the jobs")

    if add_pipeline_parameter:
        pgroup = parser.add_argument_group("Pipeline",
                                          "Pipeline execution parameters")

        pgroup.add_argument("-i", "--input", default=None, nargs="*",
                           help="The input files to run grape without creating a project")
        pgroup.add_argument("-g", "--genome", default=None,
                           help="The genome to be used in the run")
        pgroup.add_argument("-a", "--annotation", default=None,
                           help="The annotation to be used for the run")
        pgroup.add_argument("-m", "--max-mismatches", default=4,
                           help="The maximum number of mismatches allowed")
        pgroup.add_argument("-n", "--max-matches", default=10,
                           help="The maximum number of matches allowed (multimaps)")

    if add_dataset_parameter:

        if not add_pipeline_parameter:
            pgroup = parser.add_argument_group("Dataset",
                                          "Dataset information parameters")

        pgroup.add_argument("--quality", default=None,
                           help="The fastq offset for datasets quality")
        pgroup.add_argument("--read-type", dest='read_type', default=None,
                           help="The read type and length")

    if add_cluster_parameter:
        group.add_argument("-t", "--time", dest="max_time",
                            help="Maximum wall clock time")
        group.add_argument("-q", "--queue", dest="queue",
                            help="The cluster queue")
        group.add_argument("-p", "--priority", dest="priority",
                            help="The cluster priority")
        group.add_argument("-e", "--max-mem", dest="max_mem",
                            help="Maximum memory per job")
    else:
        group.add_argument("--verbose", default=False, action="store_true",
                            dest="verbose", help="Verbose job output")


def show_config(project, show_hidden=False, show_empty=False):
    """\
    Show project configuration
    """
    #from clint.textui import indent
    # print configuration
    values = project.config.get_values(exclude=['name'], show_hidden=show_hidden, show_empty=show_empty)

    if values:
        max_keys = max([len(x[0]) for x in values]) + 1
        max_values = max([len(x[1]) for x in values]) + 1

        header = str(project)
        #line = '-' * max(len(header), max_keys+max_values)

        #cli.info(line)
        cli.info(header)
        cli.info(cli.columns(['='*(max_keys-1), max_keys], ['='*(max_values-1), max_values]))
        for k, val in values:
            k = cli.colored.green(k)
            cli.info(cli.columns([k, max_keys], [val, max_values]))
        cli.info(cli.columns(['='*(max_keys-1), max_keys], ['='*(max_values-1), max_values]))
        #cli.info(line)


def list_datasets(data, tags=None, sort=None, human=False, absolute=True):
    """\
    List datasets
    """
    import json

    if tags:
        header = tags
    else:
        dataset = json.loads(data[0])
        header = dataset.keys()
    if sort:
        header = sort + [k for k in header if k not in sort]

    max_keys = [len(x)+1 for x in header]
    max_values = []
    len_values = []
    out = []
    for val in data:
        val = json.loads(val)
        if 'path' in header and not absolute:
            val['path'] = os.path.join(os.path.basename(os.path.dirname(val['path'])),os.path.basename(val['path']))
        values = [val.get(k, '-') for k in header]
        if human:
            def isnum(item):
                """\
                Check if item is a number
                """
                try:
                    float(item)
                    return True
                except Exception:
                    return False

            values = [grapeutils.human_fmt(float(v), header[1] == 'size') if isnum(v) else v for i, v in enumerate(values)]
        out.append(values)
        len_values.append([len(x)+1 for x in values])
    max_values = [max(t) for t in zip(*len_values)]


    #line = '-' * (sum([i if i>j else j for i, j in zip(max_keys,max_values)])+len(max_keys)-2)

    #cli.info(line)
    info(columns(*[[(max(max_keys[i], max_values[i])-1)*"=", max(max_keys[i], max_values[i])] for i, o in enumerate(header)]))
    info(colored.green(columns(*[[o, max(max_keys[i], max_values[i])] for i, o in enumerate(header)])))
    info(columns(*[[(max(max_keys[i], max_values[i])-1)*"=", max(max_keys[i], max_values[i])] for i, o in enumerate(header)]))
    #cli.info(line)
    for line in out:
        info(columns(*[[o, max(max_keys[i], max_values[i])] for i, o in
            enumerate(line)]))
    info(columns(*[[(max(max_keys[i], max_values[i])-1)*"=", max(max_keys[i], max_values[i])] for i, o in enumerate(header)]))
    #cli.info(line)
