#!/usr/bin/env
"""Grape default pipeline are defined in this module"""

from another.pipelines import Pipeline
import grape.tools as tools


def default_pipeline(dataset, config=None):
    """Create the grape default pipeline for the given dataset. You can
    override defaults from the configuration dictionary.

    :param dataset: the dataset
    :type dataset: grape.Dataset
    :param config: additional configuration that overrides the defaults
    :type config: dict
    """
    if config is None:
        config = {}

    index = config.get("index", None)
    annotation = config.get("annotation", None)

    if index is None:
        index = dataset.get_index()
    if annotation is None:
        annotation = dataset.get_annotation()

    pipeline = Pipeline(name="Default Pipeline %s" % (dataset.name))
    gem = pipeline.add(tools.gem())
    gem.index = index
    gem.annotation = annotation
    gem.quality = dataset.quality
    gem.output_dir = dataset.folder("mappings")
    gem.name = dataset.name
    gem.primary = dataset.primary
    if not dataset.single_end:
        gem.secondary = dataset.secondary

    flux = pipeline.add(tools.flux())
    flux.annotation = annotation
    flux.input = gem.bam
    flux.name = dataset.name
    flux.output_dir = dataset.folder("quantifications")
    return pipeline
