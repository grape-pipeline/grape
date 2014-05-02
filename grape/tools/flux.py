"""\
Flux tools
"""

from jip import tool, pipeline, Pipeline

@tool('grape_flux')
class Flux(object):
    """\
    The Flux Capacitor tool

    Usage:
        flux -i <input> -a <annotation> [-o <output_dir>] [-n <name>]

    Options:
        --help  Show this help message
        -o, --output-dir <output_dir>  The output folder [default: ${input|parent}]
        -n, --name <name>  The output prefix name

    Inputs:
        -i, --input <input>  The input file with mappings
        -a, --annotation <annotation>  The reference annotation in GTF format
    """
    def init(self):
        self.add_output('output', "${output_dir|abs}/${name}.gtf", hidden=False, long='--output', short='-o')

    def setup(self):
        self.name("flux.${name}")
        self.options['output_dir'].hidden = True
        self.options['name'].hidden = True

    def get_command(self):
        return 'bash', 'flux-capacitor ${options()}'


@tool('grape_flux_split_features')
class AwkSplitFluxFeatures(object):
    """\
    An AWK script to split the Flux Capacitor output by features

    Usage:
        split_features -i <input> [-n <name>]

    Options:
        --help  Show this help message
        -n, --name <name>  The output prefix name

    Inputs:
        -i, --input <input>  The input map file [default: stdin]
    """
    def init(self):
        self.add_output('transcript', '${input}.transcript.gtf')
        self.add_output('junction', '${input}.junction.gtf')
        self.add_output('intron', '${input}.intron.gtf')

    def setup(self):
        if self.options['name']:
            self.name("awk_split_flux_features.${name}")
            self.options['name'].hidden = True

    def get_command(self):
        command = "\'BEGIN{OFS=FS=\"\\t\"}{print > input\".\"$3\".gtf\"}\'"
        return 'bash', 'awk -v input=${input|arg("")|suf(" ")|ext} %s ${input|arg("")|suf(" ")}' % command
