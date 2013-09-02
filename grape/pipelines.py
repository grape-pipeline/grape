#!/usr/bin/env
"""Grape default pipeline are defined in this module"""

from jip.pipelines import Pipeline
from . import tools
import os

def pre_pipeline(config=None):
    """Create the grape default preprocessing pipeline. You can
    override defaults from the configuration dictionary.

    :param config: additional configuration that overrides the defaults
    :type config: dict
    """
    if config is None:
        config = {}

    genome = config.get("genome", None)
    annotation = config.get("annotation", None)
    max_length = config.get('max_length', None)
    if not max_length:
        max_length = 150

    pipeline = Pipeline(name="Default Pipeline Setup")
    gem_index = pipeline.add(tools.gem_index())
    gem_index.input = genome
    gem_index.output_dir = os.path.dirname(genome)
    gem_index.name = os.path.basename(genome)
    gem_index.hash = True

    gem_t_index = pipeline.add(tools.gem_t_index())
    gem_t_index.index = gem_index.gem
    gem_t_index.annotation = annotation
    gem_t_index.name = os.path.basename(annotation)
    gem_t_index.output_dir = os.path.dirname(annotation)
    gem_t_index.max_length = max_length
    return pipeline

def default_pipeline(project, dataset, config=None):
    """Create the grape default pipeline for the given dataset. You can
    override defaults from the configuration dictionary.

    :param dataset: the dataset
    :type dataset: grape.Dataset
    :param config: additional configuration that overrides the defaults
    :type config: dict
    """
    if config is None:
        config = {}

    index = config.get("index")
    annotation = config.get("annotation")
    quality = config.get("quality")

    if index is None:
        genome = config.get("genome")
        if genome is None:
            genome = "genome"
        index = '.'.join([genome, 'gem'])

    pipeline = Pipeline(name="Default Pipeline %s" % (dataset.id))
    gem = pipeline.add(tools.gem())
    gem.index = index
    gem.annotation = annotation
    gem.quality = quality
    gem.output_dir = project.folder("mappings", dataset.id)
    gem.name = dataset.id
    gem.primary = dataset.primary
    gem.single_end = dataset.single_end
    if not gem.single_end:
        gem.secondary = dataset.secondary

    flux = pipeline.add(tools.flux())
    flux.annotation = annotation
    flux.input = gem.bam
    flux.name = dataset.id
    flux.output_dir = project.folder("quantifications", dataset.id)
    return pipeline
