#!/usr/bin/env python
#
# test basic tools
#
from another.pipelines import Pipeline
import grape.tools as tools


def test_gem_paramters():
    p = Pipeline()
    gem = p.add(tools.gem())
    assert gem is not None
    gem.index = "/data/index.gem"
    gem.annotation = "/data/annotation.gtf"
    gem.primary = "/data/reads_1.fastq"
    gem.quality = 33
    assert gem._get_command() == '''
gemtools rna-pipeline -i /data/index.gem \
            -a /data/annotation.gtf \
            -f /data/reads_1.fastq  \
            -t 1 \
            -q 33
'''
