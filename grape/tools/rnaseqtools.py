#!/usr/bin/env python
"""\
RNAseq tools
"""

@module([("crgtools", "0.1")])
@tool('grape_pigz')
class Pigz(object):
    """\
    The parallel gzip program

    Usage:
        pigz -i <input> -o <output> [-d] [-n name]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]
        -d, --decompress  Decompress

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("pigz.${name}")
            self.options['name'].hidden = True
        self.add_option('threads', '${JIP_THREADS}', hidden=False, short='-p')

    def get_command(self):
        return 'bash', '%s ${threads|arg|suf(" ")}${decompress|arg|suf(" ")}${input|arg("-c ")|suf(" ")}${output|arg("> ")}' % bin_path(self, 'pigz')


@module([("crgtools", "0.1")])
@tool('grape_fix_se')
class AwkFixSE(object):
    """\
    An AWK script to fix SAM flags for single-end data

    Usage:
        fix_se -i <input> -o <output> [-n <name>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("awk_fix_se.${name}")
            self.options['name'].hidden = True

    def get_command(self):
        command = "\'BEGIN{OFS=FS=\"\\t\"}$0!~/^@/{split(\"1_2_8_32_64_128\",a,\"_\");for(i in a){if(and($2,a[i])>0){$2=xor($2,a[i])}}}{print}\'"
        return 'bash', 'awk %s ${input|arg("")|suf(" ")}${output|arg("> ")}' % command


@module([("crgtools", "0.1")])
@tool('grape_reverse_mate')
class AwkReverseMate(object):
    """\
    An AWK script for stranded data to reverse a mate in a SAM file.

    Usage:
        reverse_mate -i <input> -o <output> [-n <name>] [--second-mate]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name
        -o, --output <output>  The output file [default: stdout]
        --second-mate  Reverse the second mate. [default: false]

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def setup(self):
        if self.options['name']:
            self.name("awk_reverse_mate.${name}")
            self.options['name'].hidden = True
        self.add_option('mate', '128' if self.options['second_mate'] else '64')

    def get_command(self):
        command = "\'BEGIN {OFS=\"\\t\"} {if ($1!~/^@/ && and($2,${mate})>0) {$2=xor($2,0x10)}; print}\'"
        return 'bash', 'awk %s ${input|arg("")|suf(" ")}${output|arg("> ")}' % command
