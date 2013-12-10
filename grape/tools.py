#!/usr/bin/env python
"""Grape basic tools and utilities
and manage modules
"""

from jip import *


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


@tool('grape_gem_index')
class GemIndex(object):
    """
    The GEM Indexer tool

    Usage:
        gem_index -i <genome> [-o <genome_index>] [-t <threads>] [--no-hash]

    Options:
        --help  Show this help message
        -o, --output <genome_index>  The output GEM index file [default: ${input|ext}.gem]
        -t, --threads <threads>  The number of execution threads [default: 1]
        --no-hash  Do not produce the hash file [default: false]

    Inputs:
        -i, --input <genome>  The fasta file for the genome
    """

    def validate(self):
        return True

    def get_command(self):
        return "bash", "gemtools index ${options()}"


@tool('grape_gem_t_index')
class GemTranscriptomeIndex(object):
    """
    The GEM Transcrptome Indexer tool

    Usage:
        gem_t_index -i <genome_index> -a <annotation> [-m <max_read_length>] [-o <output_prefix>] [-t <threads>]

    Options:
        --help  Show this help message
        -o, --output-prefix <output_dir>  The prefix for the output files (can contain a path) [default: ${annotation|abs|parent}/${annotation}]
        -t, --threads <threads>  The number of execution threads [default: 1]
        -m, --max-length <max_read_length>  Maximum read length [default: 150]

    Inputs:
        -i, --index <genome_index>  The GEM index file for the genome
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def validate(self):
        self.add_output('gem', "%s.junctions.gem" % self.output_prefix)
        self.add_output('keys', "%s.junctions.keys" % self.output_prefix)

    def get_command(self):
        return 'bash', 'gemtools t-index ${options()}'


@tool('grape_gem_rnatool')
class gem(object):
    """
    The GEMTools RNAseq Mapping Pipeline

    Usage:
        gem -f <fastq_file>... -i <genome_index> -a <annotation> -q <quality> [-n <name>] [-o <output_dir>] [-t <threads>]

    Options:
        --help  Show this help message
        -q, --quality <quality>  The fastq offset quality
        -n, --name <name>  The output prefix name [default: ${fastq.raw()[0]|name|ext|ext|re("_[12]","")}]
        -o, --output-dir <output_dir>  The output folder
        -t, --threads <threads>  The number of execution threads [default: 1]

    Inputs:
        -f, --fastq <fastq_file>...  The input fastq
        -i, --index <genome_index>  The GEM index file for the genome
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def validate(self):
        if len(self.fastq) == 1:
            self.add_option('single_end', True, long="--single-end", hidden=False)
        self.add_output('map', "${output_dir}/${name}.map.gz")
        self.add_output('bam', "${output_dir}/${name}.bam")
        self.add_output('bai', "${output_dir}/${name}.bam.bai")

    def get_command(self):
        return 'bash','gemtools rna-pipeline ${options()}'


@tool('grape_flux')
class flux(object):
    """
    The Flux Capacitor

    Usage:
        flux -i <input> -a <annotation> [-o <output_dir>]

    Options:
        --help  Show this help message
        -o, --output-dir <output_dir>  The output folder

    Inputs:
        -i, --input <input>  The input file with mappings
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def validate(self):
        self.add_option('name',"${input|name|ext}")
        self.add_output('gtf', "${output_dir}/${name}.gtf")

    def get_command(self):
        return 'bash', 'flux-capacitor ${options()}'


@pipeline('grape_gem_setup')
class SetupPipeline(object):
    """\
    Run GEM indexers

    usage:
        setup -i <genome> -a <annotation> [-o <output_prefix>]

    Options:
        -i, --input <genome>                    The input reference genome
        -a, --annotation <annotation            The input reference annotation
        -o, --output-dir <output_dir>     The output prefix [default: ${input|abs|parent}]

    """

    def pipeline(self):
        out = self.output_dir
        input = self.input
        p = Pipeline()
        index = p.run('grape_gem_index', input=self.input, output="${out}/${input|name|ext}.gem")
        t_index = p.run('grape_gem_t_index', index=index, annotation=self.annotation, output_prefix="${out}/${annotation|name}")
        p.context(locals())
        return p


@pipeline('grape_gem_rnapipeline')
class GrapePipeline(object):
#-o, --output-dir <output_dir>  The output prefix [default: ${fastq.raw()[0]|abs|parent}]
    """
    Run the default RNAseq pipeline

    usage:
        rnaseq -f <fastq_file>... -q <quality> -i <genome_index> -a <annotation> [-o <output_dir>]

    Inputs:
        -f, --fastq <fastq_file>...   The input reference genome
        -i, --index <genome_index>    The input reference genome
        -a, --annotation <annotation  The input reference annotation

    Options:
        -q, --quality <quality>  The fatq offset quality [default: 33]
        -o, --output-dir <output_dir>  The output prefix [default: ${fastq.raw()[0]|abs|parent}]

    """
    def pipeline(self):
        p = Pipeline()
        gem = p.run('grape_gem_rnatool', index=self.index, annotation=self.annotation, fastq=self.fastq, quality=self.quality, output_dir=self.output_dir)
        flux = p.run('grape_flux', input=gem.bam, annotation=self.annotation, output_dir=self.output_dir)
        p.context(locals())
        return p


# @modules([("gemtools", "1.6.1")])
# class gem_index(Tool):
#     short_description = "The GEM indexer"
#     inputs = {
#         "input": None,
#         "name": None,
#         "output_dir": None,
#         "hash": None
#     }
#     outputs = {
#         "gem": "${output_dir}/${name}.gem",
#     }
#     command = '''
#     gemtools index -i ${input} \
#             -o ${output_dir}/${name}.gem \
#             -t ${job.threads} \
#             ${'--no-hash' if not hash else ''}
#     '''
#
#     def validate(self, args, incoming=None):
#         """Validate gem_index and make sure mandatory settings are set"""
#         errs = {}
#         if incoming is None:
#             incoming = {}
#
#         if not args.get("input"):
#             errs["input"] = "No input genome file specified!"
#         if len(errs) > 0:
#             ex = ValidationException(errs)
#             raise ex
#
# @modules([("gemtools", "1.6.1")])
# class gem_t_index(Tool):
#     short_description = "The GEM transcriptome indexer"
#     inputs = {
#         "index": None,
#         "annotation": None,
#         "name": None,
#         "output_dir": None,
#         "max_length": None
#     }
#     outputs = {
#         "gem": "${output_dir}/${name}.junctions.gem",
#         "keys": "${output_dir}/${name}.junctions.keys"
#     }
#     command = '''
#     gemtools t-index -i ${index} \
#             -a ${annotation} \
#             -m ${max_length} \
#             -t ${job.threads} \
#             -o ${output_dir}/${name}
#     '''
#
#     def validate(self, args, incoming=None):
#         """Validate gem_t_index and make sure mandatory settings are set"""
#         errs = {}
#         if incoming is None:
#             incoming = {}
#
#         if not args.get("index"):
#             errs["input"] = "No input genome file specified!"
#         if not args.get("annotation"):
#             errs["annotation"] = "No input annotation file specified!"
#
#
#         if len(errs) > 0:
#             ex = ValidationException(errs)
#             raise ex
#
# @modules([("gemtools", "1.6.1")])
# class gem(Tool):
#     short_description = "The GEMTools Mapping Pipeline"
#     inputs = {
#         "index": None,
#         "annotation": None,
#         "primary": None,
#         "secondary": "",
#         "name": None,
#         "quality": None,
#         "output_dir": None
#     }
#     outputs = {
#         "map": "${output_dir}/${name}.map.gz",
#         "bam": "${output_dir}/${name}.bam",
#         "bamindex": "${output_dir}/${name}.bam.bai",
#     }
#     command = '''
#     gemtools rna-pipeline -i ${index} \
#             -a ${annotation} \
#             -f ${primary} ${secondary} \
#             ${'--single-end' if single_end else ''} \
#             -t ${job.threads} \
#             -q ${quality} \
#             -o ${output_dir} \
#             --name ${name}
#     '''
#
#     def validate(self, args, incoming=None):
#         """Validate gem and make sure mandatory settings are set"""
#         errs = {}
#         if incoming is None:
#             incoming = {}
#
#         if not args.get("name"):
#             errs["name"] = "No name specified!"
#         if not args.get("index"):
#             errs["index"] = "No index specified!"
#         elif not os.path.exists(args["index"]):
#             errs["index"] = "Index file not found!"
#
#         if not args.get("quality"):
#             errs["quality"] = "No quality offset specified!"
#
#         if args.get("annotation"):
#             if not os.path.exists(args["annotation"]):
#                 errs["annotation"] = "Annotation file not found %s" % \
#                                      (args["annotation"])
#             transcript_index = "%s.junctions.gem" % (args["annotation"])
#             if not os.path.exists(transcript_index):
#                 errs["transcript-index"] = "No transcript index found at %s" % \
#                                            (transcript_index)
#         if len(errs) > 0:
#             ex = ValidationException(errs)
#             raise ex
#
#
# def flux_prepare_folders(tool, args):
#     """Helper function for the flux capacitor that allows to
#     check and create the output folders
#     """
#     tool.log.info("Checking output folders: %s", args['output_dir'])
#     if not os.path.exists(args['output_dir']):
#         tool.log.info("Creating output folder: %s", args['output_dir'])
#         os.makedirs(args['output_dir'])
#
#
# @modules([("flux", "1.2.3")])
# class flux(Tool):
#     short_description = "The Flux Capacitor"
#     inputs = {
#         "sortinram": True,
#         "input": None,
#         "name": None,
#         "output_dir": None
#     }
#     outputs = {
#         "gtf": "${output_dir}/${name}.gtf",
#     }
#     command = '''
#     flux-capacitor ${'-r' if sortinram else ''} \
#             -i ${input}\
#             -o ${output_dir}/${name}.gtf \
#             -a ${annotation} \
#     '''
#     on_start = [flux_prepare_folders]
#
#
#     def validate(self, args, incoming=None):
#         """Validate gem and make sure mandatory settings are set"""
#         errs = {}
#         if incoming is None:
#             incoming = {}
#
#         if not args.get("name"):
#             errs["name"] = "No name specified!"
#         if args.get("annotation"):
#             if not os.path.exists(args["annotation"]):
#                 errs["annotation"] = "Annotation file not found %s" % \
#                                      (args["annotation"])
#         else:
#             errs["annotation"] = "No annotation specified!"
#         if "input" not in incoming:
#             if args.get("input"):
#                 if not os.path.exists(args["input"]):
#                     errs["input"] = "Input BAM file not found %s" % \
#                                     (args["input"])
#             else:
#                 errs["input"] = "No input file specified!"
#
#         if len(errs) > 0:
#             ex = ValidationException(errs)
#             raise ex
