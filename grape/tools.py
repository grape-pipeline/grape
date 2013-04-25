#!/usr/bin/env python
"""Grape basic tools and utilities
and manage modules
"""
from another.tools import BashTool, ToolException
import grape.buildout
import os

class modules(object):
    """The @modueles decorator allows to decorate tool
    classes to add module dependencies
    """
    def __init__(self, modules):
        self.modules = modules

    def __call__(self, clazz):
        mods = []
        if self.modules is not None:
            # laod modules
            for m in self.modules:
                name = m[0]
                version = None
                if len(m) > 1:
                    version = m[1]
                mods.append(grape.buildout.find(name, version))
        if len(mods) > 0:
            # patch the run method
            old_run = clazz.run

            def patched(self, args):
                for m in mods:
                    m.activate()
                old_run(self, args)
            clazz.run = patched
        return clazz


@modules([("gemtools", "1.6.1")])
class gem(BashTool):
    inputs = {
        "index": None,
        "annotation": None,
        "primary": None,
        "secondary": "",
        "name": None,
        "quality": None,
        "output_dir": None
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
            -q ${quality} \
            -o ${output_dir} \
            --name ${name}
    '''

    def validate(self, args):
        """Validate gem and make sure mandatory settings are set"""
        errs = {}
        if args.get("name", None) is None:
            errs["name"] = "No name specified!"
        if args.get("quality", None) is None:
            errs["quality"] = "No quality offset specified!"
        if args.get("annotation", None) is not None:
            if not os.path.exists(args["annotation"]):
                errs["annotation"] = "Annotation file not found %s" % \
                                     (args["annotation"])
            transcript_index = "%s.junctions.gem" % (args["annotation"])
            if not os.path.exists(transcript_index):
                errs["transcript-index"] = "No transcript index found at %s" % \
                                           (transcript_index)
        if len(errs) > 0:
            ex = ToolException("Validation failed")
            ex.validation_errors = errs
            raise ex
