#!/usr/bin/env python
"""Grape basic tools and utilities
and manage modules
"""
from another.tools import BashTool


class gem(BashTool):
    inputs = {
        "index": None,
        "annotation": None,
        "primary": None,
        "secondary": "",
        "name": None,
        "quality": None
    }
    outputs = {
        "map": "${name}.map.gz",
        "bam": "${name}.bam",
        "bamindex": "${name}.bam.bai",
    }
    command = '''
    gemtools rna-pipeline -i ${index} \
            -a ${annotation} \
            -f ${primary} ${secondary} \
            -t ${job.threads} \
            -q ${quality}
    '''
