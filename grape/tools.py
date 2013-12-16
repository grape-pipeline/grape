#!/usr/bin/env python
"""Grape basic tools and utilities
and manage modules
"""

from jip import *
from buildout import module


@module([("gemtools", "1.6.1")])
@tool('grape_gem_index')
class GemIndex(object):
    """\
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

@module([("gemtools", "1.6.1")])
@tool('grape_gem_t_index')
class GemTranscriptomeIndex(object):
    """\
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


@module([("gemtools", "1.6.1")])
@tool('grape_gem_rnatool')
class gem(object):
    """\
    The GEMtools RNAseq Mapping Pipeline

    Usage:
        gem -f <fastq_file> -i <genome_index> -a <annotation> -q <quality> [-n <name>] [-o <output_dir>] [-t <threads>] [--single-end]

    Options:
        --help  Show this help message
        -q, --quality <quality>  The fastq offset quality
        -n, --name <name>  The output prefix name [default: ${fastq|name|ext|ext|re("_[12]","")}]
        -o, --output-dir <output_dir>  The output folder
        -t, --threads <threads>  The number of execution threads [default: 1]
        -s, --single-end    Run the single-end pipeline

    Inputs:
        -f, --fastq <fastq_file>  The input fastq
        -i, --index <genome_index>  The GEM index file for the genome
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def validate(self):
        self.add_output('map', "${output_dir}/${name}.map.gz")
        self.add_output('bam', "${output_dir}/${name}.bam")
        self.add_output('bai', "${output_dir}/${name}.bam.bai")

    def get_command(self):
        return 'bash','gemtools rna-pipeline ${options()}'


@module([("flux", "1.2.3")])
@tool('grape_flux')
class flux(object):
    """\
    The Flux Capacitor tool

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
    The GEM indexes setup pipeline

    usage:
        setup -i <genome> -a <annotation> [-o <output_prefix>]

    Options:
        -i, --input <genome>              The input reference genome
        -a, --annotation <annotation      The input reference annotation
        -o, --output-dir <output_dir>     The output prefix

    """

    def pipeline(self):
        out = self.output_dir
        if not out:
            out_genome = "${input|ext}.gem"
            out_tx = "${annotation}"
        else:
            out_genome = out_tx = out
        input = self.input
        p = Pipeline()

        index = p.run('grape_gem_index', input=self.input, output=out_genome)
        t_index = p.run('grape_gem_t_index', index=index, annotation=self.annotation, output_prefix=out_tx)
        p.context(locals())
        return p


@pipeline('grape_gem_rnapipeline')
class GrapePipeline(object):
#-o, --output-dir <output_dir>  The output prefix [default: ${fastq.raw()[0]|abs|parent}]
    """\
    The default GRAPE RNAseq pipeline

    usage:
        rnaseq -f <fastq_file_1> -f <fastq_file_2> -q <quality> -i <genome_index> -a <annotation> [-o <output_dir>] [--single-end]

    Inputs:
        -f, --fastq <fastq_file>        The input reference genome
        -i, --index <genome_index>      The input reference genome
        -a, --annotation <annotation    The input reference annotation

    Options:
        -q, --quality <quality>         The fastq offset quality [default: 33]
        -s, --single-end                Run the single-end pipeline
        -o, --output-dir <output_dir>   The output prefix [default: ${fastq|abs|parent}]

    """
    def pipeline(self):
        p = Pipeline()
        gem = p.run('grape_gem_rnatool', index=self.index, single_end=self.single_end, annotation=self.annotation, fastq=self.fastq, quality=self.quality, output_dir=self.output_dir)
        flux = p.run('grape_flux', input=gem.bam, annotation=self.annotation, output_dir=self.output_dir)
        p.context(locals())
        return p
