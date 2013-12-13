"""Grape command line utilities
"""
from clint.textui import colored, puts, columns
import grape.commands
import jip
from grape.grape import Grape

def jip_prepare(args):
    # get the project and the selected datasets
    project, datasets = get_project_and_datasets(args)
    jip_db_file = project.config.get('jip.db')
    if jip_db_file:
        # setup jip db
        jip.db.init(jip_db_file)
    p = jip.Pipeline()
    jargs = {}
    if datasets == ['setup']:
        jargs['input'] = project.config.get('genome')
        jargs['annotation'] = project.config.get('annotation')
        p.run('grape_gem_setup', **jargs)
        jobs = jip.jobs.create_jobs(p)
    else:
        jargs['fastq'] = [d.fastq.keys()[0] for d in datasets]
        jargs['annotation'] = project.config.get('annotation')
        jargs['index'] = project.config.get('genome')+'.gem'
        p.run('grape_gem_rnapipeline', **jargs)
        jobs = jip.jobs.create_jobs(p)
    return jobs

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
        raise grape.commands.CommandError("No datasets specified!")
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
        group.add_argument("-m", "--max-mem", dest="max_mem",
                            help="Maximum memory per job")
    else:
        group.add_argument("--verbose", default=False, action="store_true",
                            dest="verbose", help="Verbose job output")