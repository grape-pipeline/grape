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
        "map": "${output_dir}/${name}.map.gz",
        "bam": "${output_dir}/${name}.bam",
        "bamindex": "${output_dir}/${name}.bam.bai",
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

    def validate(self, args, incoming=None):
        """Validate gem and make sure mandatory settings are set"""
        errs = {}
        if incoming is None:
            incoming = {}

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


def flux_prepare_folders(tool, args):
    tool.log.info("Checking output folders: %s", args['output_dir'])
    if not os.path.exists(args['output_dir']):
        tool.log.warn("Creating output folder: %s", args['output_dir'])
        os.makedirs(args['output_dir'])


@modules([("flux", "1.2.3")])
class flux(BashTool):
    inputs = {
        "sortinram": True,
        "input": None,
        "name": None,
        "output_dir": None
    }
    outputs = {
        "map": "${name}.map.gz",
        "bam": "${name}.bam",
        "bamindex": "${name}.bam.bai",
    }
    command = '''
    flux-capacitor ${'-r' if sortinram else ''} \
            -i ${input}\
            -o ${output_dir}/${name}.gtf \
            -a ${annotation} \
    '''
    on_start = [flux_prepare_folders]


    def validate(self, args, incoming=None):
        """Validate gem and make sure mandatory settings are set"""
        errs = {}
        if incoming is None:
            incoming = {}

        if args.get("name", None) is None:
            errs["name"] = "No name specified!"
        if args.get("annotation", None) is not None:
            if not os.path.exists(args["annotation"]):
                errs["annotation"] = "Annotation file not found %s" % \
                                     (args["annotation"])
        else:
            errs["annotation"] = "No annotation specified!"
        if "input" not in incoming:
            if args.get("input") is not None:
                if not os.path.exists(args["input"]):
                    errs["input"] = "Input BAM file not found %s" % \
                                    (args["input"])
            else:
                errs["input"] = "No input file specified!"

        if len(errs) > 0:
            ex = ToolException("Validation failed")
            ex.validation_errors = errs
            raise ex
