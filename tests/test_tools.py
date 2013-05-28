#!/usr/bin/env python
#
# test basic tools
#
from jip.pipelines import Pipeline
import grape.tools as tools
from jip.tools import ValidationException

import pytest


def test_gem_paramters():
    p = Pipeline()
    gem = p.add(tools.gem())
    assert gem is not None
    gem.index = "/data/index.gem"
    gem.annotation = "/data/annotation.gtf"
    gem.primary = "/data/reads_1.fastq"
    gem.quality = 33
    cfg = gem.get_configuration()
    assert cfg["index"] == "/data/index.gem"
    assert cfg["annotation"] == "/data/annotation.gtf"
    assert cfg["primary"] == "/data/reads_1.fastq"
    assert cfg["quality"] == 33


def test_gem_validation_no_name():
    p = Pipeline()
    gem = p.add(tools.gem())

    with pytest.raises(ValidationException) as err:
        gem.validate()
    ex = err.value
    assert ex.errors["name"] == "No name specified!"


def test_gem_validation_no_quality():
    p = Pipeline()
    gem = p.add(tools.gem())

    with pytest.raises(ValidationException) as err:
        gem.validate()
    ex = err.value
    assert ex.errors["quality"] == "No quality offset specified!"


def test_gem_validation_no_transcript_index():
    p = Pipeline()
    gem = p.add(tools.gem())
    gem.annotation = "/data/annotations/annotation.gtf"

    with pytest.raises(ValidationException) as err:
        gem.validate()
    ex = err.value
    assert ex.errors["transcript-index"] == "No transcript index found at /data/annotations/annotation.gtf.junctions.gem"
