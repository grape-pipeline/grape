#!/usr/bin/env python
"""Grape basic tools and utilities
and manage modules
"""
from jip.tools import Tool, ValidationException
import os


class modules(object):
    """The @modules decorator allows to decorate tool
    classes to add module dependencies
    """
    def __init__(self, modules):
        self.modules = modules

    def _load_modules(self, mods):
        from . import buildout
        # laod modules
        for m in self.modules:
            name = m[0]
            version = None
            if len(m) > 1:
                version = m[1]
            mods.append(buildout.find(name, version))

    def __call__(self, clazz):
        if self.modules is not None:
            # patch the run method
            old_run = clazz.run
            clazz.modules = self.modules
            clazz._load_modules = self._load_modules

            def patched(self, args):
                mods = []
                self._load_modules(mods)
                for m in mods:
                    m.activate()
                old_run(self, args)
            clazz.run = patched
        return clazz

@modules([("gemtools", "1.6.1")])
class gem_index(Tool):
    short_description = "The GEM indexer"
    inputs = {
        "input": None,
        "name": None,
        "output_dir": None,
        "hash": None
    }
    outputs = {
        "gem": "${output_dir}/${name}.gem",
    }
    command = '''
    gemtools index -i ${input} \
            -o ${output_dir}/${name}.gem \
            -t ${job.threads} \
            ${'--no-hash' if not hash else ''}
    '''

    def validate(self, args, incoming=None):
        """Validate gem_index and make sure mandatory settings are set"""
        errs = {}
        if incoming is None:
            incoming = {}

        if args.get("input", None) is None:
            errs["input"] = "No input genome file specified!"
        if len(errs) > 0:
            ex = ValidationException(errs)
            raise ex

@modules([("gemtools", "1.6.1")])
class gem_t_index(Tool):
    short_description = "The GEM transcriptome indexer"
    inputs = {
        "index": None,
        "annotation": None,
        "name": None,
        "output_dir": None,
        "max_length": None
    }
    outputs = {
        "gem": "${output_dir}/${name}.junctions.gem",
        "keys": "${output_dir}/${name}.junctions.keys"
    }
    command = '''
    gemtools t-index -i ${index} \
            -a ${annotation} \
            -m ${max_length} \
            -t ${job.threads} \
            -o ${output_dir}/${name}
    '''

    def validate(self, args, incoming=None):
        """Validate gem_t_index and make sure mandatory settings are set"""
        errs = {}
        if incoming is None:
            incoming = {}

        if args.get("index", None) is None:
            errs["input"] = "No input genome file specified!"
        if args.get("annotation", None) is None:
            errs["annotation"] = "No input annotation file specified!"


        if len(errs) > 0:
            ex = ValidationException(errs)
            raise ex

@modules([("gemtools", "1.6.1")])
class gem(Tool):
    short_description = "The GEMTools Mapping Pipeline"
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
            ex = ValidationException(errs)
            raise ex


def flux_prepare_folders(tool, args):
    """Helper function for the flux capacitor that allows to
    check and create the output folders
    """
    tool.log.info("Checking output folders: %s", args['output_dir'])
    if not os.path.exists(args['output_dir']):
        tool.log.info("Creating output folder: %s", args['output_dir'])
        os.makedirs(args['output_dir'])


@modules([("flux", "1.2.3")])
class flux(Tool):
    short_description = "The Flux Capacitor"
    inputs = {
        "sortinram": True,
        "input": None,
        "name": None,
        "output_dir": None
    }
    outputs = {
        "gtf": "${output_dir}/${name}.gtf",
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
            ex = ValidationException(errs)
            raise ex
