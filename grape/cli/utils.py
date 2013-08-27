"""Grape command line utilities
"""
from clint.textui import colored, puts, columns
from jip.pipelines import PipelineException
import grape.commands
from grape.grape import Grape


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

    metadata = {'type':'fastq'}
    datasets = None

    project = Project.find()
    if project is None or not project.exists():
        project = Project(os.getcwd())
        project.initialize()
        if 'genome' in args and args.genome:
            project.config.set('genome',os.path.abspath(args.genome),
                                commit=True)
            #args.genome = project.config.get('genome')
        if 'annotation' in args and args.annotation:
            project.config.set('annotation',os.path.abspath(args.annotation),
                                commit=True)
            #args.annotation = project.config.get('annotation')
        if 'quality' in args and args.quality:
            project.config.set('quality', args.quality)
            metadata['quality'] = args.quality

        if 'read_type' in args and args.read_type:
            metadata['readType'] = args.read_type

    if 'input' in args and args.input:
        ds = {}
        for dataset in args.input:
            if Project.find(dataset):
                name, files = Project.find(dataset)
                ds[name] = files
        for name, files in ds.items():
            metadata['id'] = name
            if len(files) > 1 and not 'readType' in m:
                metadata['readType'] = '2x'
            for f in files:
                metadata['path'] = f
                project.index.insert(**metadata)
            project.save()
        datasets = project.get_datasets(id=ds.keys())

    if "datasets" in args and not datasets:
        datasets = args.datasets
    else:
        datasets = ["all"]

    if datasets is None:
        raise grape.commands.CommandError("No datasets specified!")
    if datasets == ['all']:
        datasets = []

    datasets = project.get_datasets(id=datasets)

    return (project, datasets)


def add_default_job_configuration(parser, add_cluster_parameter=True, add_pipeline_parameter=True):
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

def _prepare_pipeline(pipeline):
    """Validate the pipeline and prints
    the validation errors in case there are any.
    """
    import logging
    log = logging.getLogger("grape")
    log.info("Preparing pipeline: %s", pipeline)
    try:
        pipeline.validate()
        return True
    except PipelineException, e:
        # print error messages and return false
        puts(colored.red("Error while validating pipeline"))
        for step, errs in e.validation_errors.items():
            puts(colored.red("Validation error in step: %s" % (step)))
            for field, desc in errs.items():
                puts("\t" + columns([colored.red(field), 30], [desc, None]))
        return False


def create_pipelines(pipeline_fun, project, datasets, configuration):
    """Create a pipeline for each dataset using the passed pipeline_fun
    functions. The pipeline_fun function must be a function that
    takes a :py:class:`grape.Dataset` and a configuration dict
    and return a :py:class:jip.pipelines.Pipeline.

    :param pipeline_fun: the pipeline creation function
    :type pipeline_fun: function
    :param datasets: list of datasets
    :type datasets: list
    :param project: the grape project
    :type project: grape.Project
    :param configuration: additional configuration dictionary
    :type configuration: dict
    :returns pipelines: list of pipelines
    :rtype pipelines: list
    """
    from grape.grape import Grape
    pipelines = []
    grp = Grape()

    genome = configuration.get('genome', None)
    annotation = configuration.get('annotation', None)
    quality = configuration.get('quality', None)

    if not genome:
        genome = project.config.get('genome')
        configuration['genome'] = genome
    if not annotation:
        annotation = project.config.get('annotation')
        configuration['annotation'] = annotation
    if not quality:
        quality = project.config.get('quality')
        configuration['quality'] = quality

    for d in datasets:
        if d:
            if not configuration.get('genome', None):
                configuration['genome'] = d.get_genome(project.config)
            if not configuration.get('annotation', None):
                configuration['annotation'] = d.get_annotation(project.config)
            if not configuration.get('quality', None):
                configuration['quality'] = d.quality
            pipeline = pipeline_fun(d, configuration)
        else:
            pipeline = pipeline_fun(configuration)
        # validate the pipeline
        if not _prepare_pipeline(pipeline):
            return False
        pipelines.append(pipeline)
        # update job params
        if configuration is not None:
            for step in pipeline.tools.values():
                grp.configure_job(step, project, d, configuration)

    return pipelines
