"""\
Gem tools and pipelines
"""
import os
from jip import tool, pipeline, Pipeline

@tool('grape_gem_index')
class GemIndex(object):
    """\
    The GEM Indexer tool

    Usage:
        grape_gem_index -i <genome> [-o <genome_index>] [--no-hash]

    Options:
        --help  Show this help message
        -o, --output <genome_index>  The output GEM index file [default: ${input|ext}.gem]
        --no-hash  Do not produce the hash file [default: false]

    Inputs:
        -i, --input <genome>  The fasta file for the genome
    """
    def setup(self):
        self.name('index.${input|name|ext}')
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def get_command(self):
        return "bash", "gemtools index ${options()}"


@tool('grape_gem_t_index')
class GemTranscriptomeIndex(object):
    """\
    The GEM Transcrptome Indexer tool

    Usage:
        grape_gem_t_index -i <genome_index> -a <annotation> [-m <max_read_length>] [-o <output_prefix>]

    Options:
        --help  Show this help message
        -o, --output-prefix <output_dir>  The prefix for the output files (can contain a path) [default: ${annotation|abs|parent}/${annotation}]
        -m, --max-length <max_read_length>  Maximum read length [default: 150]

    Inputs:
        -i, --index <genome_index>  The GEM index file for the genome
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def init(self):
        self.add_output('gem', "${output_prefix}.junctions.gem")
        self.add_output('keys', "${output_prefix}.junctions.keys")
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def setup(self):
        self.name('t_index.${index|name|ext}')

    def get_command(self):
        return 'bash', 'gemtools t-index ${options()}'


@tool('grape_gem_rna_pipeline')
class Gem(object):
    """\
    The GEMtools RNAseq Mapping Pipeline

    Usage:
        grape_gem_rnapipeline -f <fastq_file> -i <genome_index> -r <transcript_index> -q <quality> [-n <name>] [-o <output_dir>] [--single-end] [--no-bam] [--no-stats]

    Options:
        --help  Show this help message
        -q, --quality <quality>  The fastq offset quality
        -n, --name <name>  The output prefix name [default: ${fastq|name|ext|ext|re("[_-][12]","")}]
        -o, --output-dir <output_dir>  The output folder
        -s, --single-end    Run the single-end pipeline
        --no-bam  Do not generate the BAM file
        --no-stats  Do not generate mapping statistics

    Inputs:
        -f, --fastq <fastq_file>  The input fastq
        -i, --index <genome_index>  The GEM index file for the genome
        -r, --transcript-index <trascript_index>  The GEM index file for the transcriptome
    """
    def init(self):
        self.add_output('map', "${output_dir}/${name}.map.gz")

    def setup(self):
        self.name("gem.${name}")
        if not self.options['no_bam']:
            self.add_output('bam', "${output_dir}/${name}.bam")
            self.add_output('bai', "${output_dir}/${name}.bam.bai")
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def get_command(self):
        return 'bash', 'gemtools rna-pipeline ${options()}'


@tool('grape_gem_quality')
class GemQuality(object):
    """\
    The GEMtools quality filter program

    Usage:
        grape_gem_quality [-i <input>] [-o <output>] [-n name]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("gem.quality.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def get_command(self):
        return 'bash', 'gt.quality ${options()}'

@tool('grape_gem_filter')
class GemFilter(object):
    """\
    The GEMtools general filter program

    Usage:
        grape_gem_filter [-i <input>] [-o <output>] [-n name] [--max-levenshtein-error <error>] [--max-matches <matches>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]
        --max-levenshtein-error <error>  The maximum number of edit operations allowed
        --max-matches <matches>  The maximum number of matches allowed

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("gem.filter.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def get_command(self):
        return 'bash', 'gt.filter ${options()}'


@tool('grape_gem_stats')
class GemStats(object):
    """\
    The GEMtools stats program

    Usage:
        grape_gem_stats -i <input> [-a] [-p] [-n name]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -a, --all-tests  Perform all tests
        -p, --paired-end  Use paired-end information

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name'].value:
            self.name("gem.stats.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-t')

    def get_command(self):
        return 'bash', 'gt.stats ${options()}'


@tool('grape_gem_sam')
class GemSam(object):
    """\
    The GEMtools SAM conversion program

    Usage:
        grape_gem_sam [-f <input>] [-o <output>] -i <genome_index> -q <quality> [-l] [--read-group <read_group>] [--expect-single-end-reads] [--expect-paired-end-reads] [-n name]

    Options:
        --help  Show this help message
        -o, --output <output>  The output file [default: stdout]
        -n, --name <name>  The output prefix name
        -i, --index <genome_index>  The gem index for the genome
        -q, --quality <quality>  The quality offset
        -l, --sequence-lengths  Add sequence length to SAM header
        --read-group <read_group>  Add read group information
        --expect-single-end-reads  Override automatic SE/PE detection
        --expect-paired-end-reads  Override automatic SE/PE detection
    Inputs:
        -f, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name'].value:
            self.name("gem.sam.${name}")
            self.options['name'].hidden = True
        self.options['index'].short = '-I'
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-T')
        try:
            int(self.options['quality'].raw())
            self.options['quality'] = 'offset-%s' % self.options['quality'].raw()
        except:
            pass

    def get_command(self):
        return 'bash', 'gem-2-sam ${options()}'


@pipeline('grape_gem_setup')
class SetupPipeline(object):
    """\
    The GEM indexes setup pipeline

    usage:
        grape_gem_setup -i <genome> -a <annotation> [-o <output_prefix>]

    Options:
        -i, --input <genome>              The input reference genome
        -a, --annotation <annotation      The input reference annotation
        -o, --output-dir <output_dir>     The output prefix

    """
    def init(self):
        self.add_output('index', '')
        self.add_output('t_out', '')
        self.add_output('t_index', '')

    def setup(self):
        self.name('grape_gem_setup')
        out = self.output_dir
        if not out:
            index = "${input|ext}.gem"
            t_out = "${annotation}"
        else:
            index = "%s/${input|name|ext}.gem" % out
            t_out = "%s/${annotation|name}" % out
        self.options['index'] = index
        self.options['t_out'] = t_out
        self.options['t_index'] = t_out+'.gem'

    def pipeline(self):
        p = Pipeline()
        index = p.run('grape_gem_index', input=self.input, output=self.index)
        p.run('grape_gem_t_index', index=index, annotation=self.annotation, output_prefix=self.t_out)
        return p

@pipeline('grape_gem_filter_pipeline')
class FilterPipeline(object):
    """\
    The GEM filter pipeline

    usage:
         grape_gem_filter_pipeline -i <map_file> --max-mismatches <mismatches>
                             --max-matches <matches> [-o <output>] [-l <name>]

    Inputs:
        -i, --input <map_file>        The input MAP file

    Options:
        -l, --name <name>  Prefix name
        -o, --output <output>  The output file [default: ${input|ext|ext}_m${max_mismatches}_n${max_matches}.map.gz]
        -m, --max-mismatches <mismatches>  The maximum number of edit
                                           operations allowed
        -n, --max-matches <matches>  The maximum number of matches allowed

    """
    def setup(self):
        self.name('grape_gem_filter_pipeline')

    def pipeline(self):
        p = Pipeline()
        sample=self.options['name']
        gem_filter = p.run('grape_gem_quality', input=self.input, name=sample) | \
        p.run('grape_gem_filter', max_levenshtein_error=self.max_mismatches, name=sample) | \
        p.run('grape_gem_filter', max_matches=self.max_matches, name=sample) | \
        p.run('grape_pigz', output=self.output, name=sample)
        return p

@pipeline('grape_gem_bam_pipeline')
class Gem2BamPipeline(object):
    """\
    The GEM to BAM conversion pipeline

    usage:
         grape_gem_bam_pipeline [-f <map_file>] -i <gem_index> -q quality -o <output> [-s] [-l] [--read-group <read_group>] [-n <name>]

    Inputs:
        -f, --input <map_file>        The input MAP file [default: stdin]
        -i, --index <gem_index>        The gem index for the genome

    Options:
        -n, --name <name>  Prefix name
        -s, --single-end  Expect single end input
        -q, --quality <quality>  The quality offset
        -l, --sequence-lengths  Add sequence lengths information to SAM header
        -o, --output <output>  The output file [default: ${input|ext|ext}.bam]
    """
    def init(self):
        self.add_output('bam', '${output}')
        self.add_output('bai', '${output}.bai')

    def setup(self):
        self.name('grape_gem_bam_pipeline')

    def pipeline(self):
        p = Pipeline()
        sample=self.options['name']
        gem_bam = p.run('grape_pigz', input=self.input, decompress=True, name=sample) | \
        p.run('grape_gem_sam', index=self.index, read_group=self.read_group, quality=self.quality, sequence_lengths=self.sequence_lengths, expect_paired_end_reads=not self.single_end, expect_single_end_reads=self.single_end, name=sample) | \
        p.run('grape_samtools_view', input_sam=True, output_bam=True, name=sample) | \
        p.run('grape_samtools_sort', output=self.output, name=sample)
        gem_bai = p.run('grape_samtools_index', input=gem_bam.output, name=sample)
        return p


@pipeline('grape_gem_mapping_pipeline')
class GemMappingPipeline(object):
    """\
    The GEM mapping pipeline

    Usage:
        grape_gem_mapping_pipeline -f <fastq_file> -g <genome_file> -a
        <annotation_file> -m <max_mismatches> -n <max_matches> [-o
        <output_dir>] [-s] [-k] [-q <quality_offset>]

    Inputs:
        -f, --fastq <fastq_file>                The input sequences in FASTQ
                                                format
        -g, --genome <genome_file>              The reference genome in FASTA
                                                format
        -a, --annotation <annotation_file>      The reference annotation in
                                                GTF format

    Options:
        -o, --output-dir <output_dir>           The folder where to store the
                                                output
                                                [default: ${fastq|abs|parent}]
        -q, --quality <quality_offset>          The fastq quality offset
                                                [default: 33]
        -k, --keep-temp                         Keep intermediate files
        -s, --single-end                        Run the pipeline for
                                                single-end data
        -m, --max-mismatches <max_mismatches>   The maximum number of
                                                mismatches allowed
        -n, --max-matches <max_matches>         The maximum number of
                                                multimaps allowed
    """

    def init(self):
        self.add_option('sample', '${fastq|name|ext|ext|re("[_-][12]","")}')
        self.add_output('bam',
                        os.path.join(self.output_dir.get(), '${sample}.bam'))

    def setup(self):
        pass

    def pipeline(self):
        p = Pipeline()
        temp = (not self.keep_temp)
        gem_setup = p.run('grape_gem_setup', input=self.genome, annotation=self.annotation)
        gem = p.job(temp=temp).run('grape_gem_rna_pipeline', index=gem_setup.index, transcript_index=gem_setup.t_index, single_end=self.single_end, fastq=self.fastq, quality=self.quality, no_bam=True, no_stats=True,
            output_dir=self.output_dir.get())
        sample = self.sample
        gem_filter = p.job(temp=temp).run('grape_gem_filter_pipeline', input=gem.map, max_mismatches=self.max_mismatches, max_matches=self.max_matches, name=sample)
        gem_bam = p.run('grape_gem_bam_pipeline', input=gem_filter.output, index=gem_setup.index, quality=self.quality, single_end=self.single_end, sequence_lengths=True, name=sample,
            output=self.bam)
        p.context(locals())
        return p
