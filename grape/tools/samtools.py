#!/usr/bin/env python
"""\
"""

@module([("samtools", "0.1.19")])
@tool('grape_samtools_view')
class SamtoolsView(object):
    """\
    The SAMtools view program

    Usage:
        sam.view -i <input> -o <output> [-s] [-b] [-n <name>]

    Options:
        --help  Show this help message
        -s, --input-sam  Read input in SAM format
        -b, --output-bam  Output BAM format
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("sam.view.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-@')
        self.options['input_sam'].short = "-S"

    def get_command(self):
        return 'bash', '%s ${input_sam|arg|suf(" ")}${output_bam|arg|suf(" ")}${threads|arg|suf(" ")}${input|arg("")|else("-")|suf(" ")}${output|arg("> ")}' % bin_path(self, 'samtools view')


@module([("samtools", "0.1.19")])
@tool('grape_samtools_sort')
class SamtoolsSort(object):
    """\
    The SAMtools sort program

    Usage:
        sam.sort -i <input> -o <output> [-m <max_memory>] [-n <name>]

    Options:
        --help  Show this help message
        -m, --max-memory <max_memory>  The maximum amount of RAM to use for sorting (per thread)
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: ${input|ext}_sorted.bam]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("sam.sort.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-@')

    def get_command(self):
        return 'bash', '%s ${threads|arg|suf(" ")}${max_memory|arg|suf(" ")}${input|arg("")|else("-")|suf(" ")}${output|arg("")|ext}' % bin_path(self, 'samtools sort')


@module([("samtools", "0.1.19")])
@tool('grape_samtools_index')
class SamtoolsIndex(object):
    """\
    The SAMtools index program

    Usage:
        sam.index -i <input> -o <output> [-n <name>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: ${input|abs}.bai]

    Inputs:
        -i, --input <input>  The input map file
    """
    def setup(self):
        if self.options['name']:
            self.name("sam.index.${name}")
            self.options['name'].hidden = True


    def get_command(self):
        return 'bash', '%s ${input|arg("")|suf(" ")}${output|arg("")}' % bin_path(self, 'samtools index')
