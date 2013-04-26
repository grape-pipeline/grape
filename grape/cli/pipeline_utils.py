#!/usr/bin/env python
"""Grape command line utillitis and helper functions

This module contains all the little helpers that can be used by the
grape command line command. Functions here might print to system out or
error streams and wrap around functions that are already implemented
somewhere else but need to output thing to the console or do things
that are specific the a command line execution.
"""
import logging

from clint.textui import colored, puts, columns
from another.pipelines import PipelineException

# we use the general grape logger
log = logging.getLogger("grape")


def prepare_pipeline(project, pipeline):
    """Takes a project and a pipeline and tries to prepare
    the pipeline by performing validation and printing error
    messages. Exceptions are catched here and the method
    return True if preperation was successfull, False otherwise.
    """
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
