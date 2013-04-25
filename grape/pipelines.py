#!/usr/bin/env
"""Grape default pipeline are defined in this module"""

from another.pipelines import Pipeline
import grape.tools as tools


def default_pipeline(dataset, index, annotation, threads=1):
    pipeline = Pipeline(name="default_pipeline")
    gem = pipeline.add(tools.gem())
    gem.index = index
    gem.annotation = annotation
    gem.quality = dataset.quality
    gem.output_dir = dataset.folder("mappings")
    gem.name = dataset.name
    gem.primary = dataset.primary
    gem.job.threads = threads
    if not dataset.single_end:
        gem.secondary = dataset.secondary
    return pipeline
