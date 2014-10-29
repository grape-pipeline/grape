#!/usr/bin/env python
"""\
BEDtools
"""

from jip import tool, pipeline, Pipeline

@tool('grape_bedtools_genomecov')
class BedtoolsGenomeCov(object):
    """\
    The BEDtools genomeCoverage program

    Usage:
        grape_bedtools_genomecov -i <input> -o <output> [-s <strand>] [--bam] [-b] [--split] [-n <name>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]
        -b, --bed-graph  Report depth in BedGraph format
        -s, --strand <strand>  Calculate coverage of intervals from a specific strand
        --split  Treat "split" BAM or BED12 entries as distinct BED intervals
        --bam  Input is in BAM format

    Inputs:
        -i, --input <input>  The input map file [default: stdin]

    """

    def setup(self):
        if self.options['name']:
            self.name("bed.gencov.${name}")
            self.options['name'].hidden = True
        if self.options['bam']:
            self.options['input'].short = '-ibam'
        self.options['bed_graph'].short = "-bg"
        self.options['split'].short = "-split"
        self.options['strand'].short = "-strand"

    def get_command(self):
        return 'bash', 'bedtools genomecov ${bed_graph|arg|suf(" ")}${split|arg|suf(" ")}${strand|arg|suf(" ")}${input|arg|else(input.short+" stdin")|suf(" ")}${output|arg("> ")}'


@tool('grape_bedGraphToBigWig')
class BedgraphBigwig(object):
    """\
    The bedGraphToBigWig program

    Usage:
        grape_bedGraphToBigWig -i <input> -o <output> -g <genome_fai> [-n <name>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
        -g, --genome <genome_fai>  The genome chromosme sizes

    """

    def setup(self):
        if self.options['name']:
            self.name("bed.bgtobw.${name}")
            self.options['name'].hidden = True

    def get_command(self):
        return 'bash', 'bedGraphToBigWig ${input|arg("")|else("-")|suf(" ")}${genome|arg("")|suf(" ")}${output|arg("")}'


@pipeline('grape_bigwig_pipeline')
class BigwigPipeline(object):
    """\
    The Bigwig pipeline

    usage:
         grape_bigwig_pipeline -i <bam_file> -o <bw_file> -g <genome_file> [--stranded] [ --reverse-first-mate | --reverse-second-mate ]

    Inputs:
        -i, --input <bam_file>        The input MAP file
        -g, --genome <genome_file>    The genome chromosome sizes file

    Options:
        -n, --name <name>  Prefix name
        -o, --output <bw_file>  The output file [default: ${input|ext}.bw
        --stranded  Whether the data is stranded
        --reverse-first-mate  Reverse the first mate in the bam file
        --reverse-second-mate  Reverse the second mate in the bam file
    """
    def setup(self):
        self.name('bigwig.pipeline')

    def pipeline(self):
        p = Pipeline()
        sample=self.options['name']
        bam = self.input
        strands = {'-':'minusRaw','+':'plusRaw'}
        second_mate = False
        reverse_mate = False

        if self.options['reverse_first_mate']:
            reverse_mate = True
        if self.options['reverse_second_mate']:
            second_mate = True
            reverse_mate = True
        if reverse_mate:
            bam = p.run('grape_samtools_view', input=bam, name=sample) | \
                  p.run('grape_reverse_mate', input=self.input, name=sample, second_mate=second_mate) | \
                  p.run('grape_samtools_view', input_sam=True, output_bam=True, name=sample)
        bedgraph = p.job(temp=True).run('grape_bedtools_genomecov', input=bam, output="${inp|ext}_${strands.get(strand.raw())}.bedgraph", bam=True, split=True, bed_graph=True, strand = "" if not self.stranded else ["+", "-"])
        p.run('grape_bedGraphToBigWig', input=bedgraph.output, genome=self.genome, output='${input|ext}.bw')
        p.context(locals())
        return p
