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

    project = Project.find()
    if project is None or not project.exists():
        raise grape.commands.CommandError("No grape project found!")

    datasets = None
    if "datasets" in args:
        datasets = args.datasets
        if datasets is None:
            raise grape.commands.CommandError("No datasets specified!")
        if datasets == ['all']:
            datasets = []
        datasets = project.get_datasets(query_list=datasets)

    return (project, datasets)


def add_default_job_configuration(parser, add_cluster_parameter=True):
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
    for d in datasets:
        pipeline = pipeline_fun(d, project.config)

        # validate the pipeline
        if not _prepare_pipeline(pipeline):
            return False
        pipelines.append(pipeline)
        # update job params
        if configuration is not None:
            for step in pipeline.tools.values():
                grp.configure_job(step, project, d, configuration)
    return pipelines
