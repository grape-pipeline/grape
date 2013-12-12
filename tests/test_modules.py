import pytest
import os
from grape.buildout import module
from grape.grape import Grape
import jip

def test_module_decorator():
    @module([("gemtools", "1.6.1")])
    @jip.tool('gemtools_test')
    class gemtools(object):
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


    j = os.path.join

    p = jip.Pipeline()
    p.run('gemtools_test', input='genome.fa')

    path = j('/','modules','gemtools','1.6.1','gemtools')

    jobs = jip.create_jobs(p, validate=False)

    assert len(jobs) == 1
    assert jobs[0] is not None
    assert jobs[0].command.split()[0] == path

def test_module_decorator_with_grape_home():
    @module([("gemtools", "1.6.1")])
    @jip.tool('gemtools_test')
    class gemtools(object):
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


    j = os.path.join

    p = jip.Pipeline()
    p.run('gemtools_test', input='genome.fa')

    os.environ['GRAPE_HOME'] = '/home/grape'

    path = j(Grape().home,'modules','gemtools','1.6.1','gemtools')

    jobs = jip.create_jobs(p, validate=False)

    assert len(jobs) == 1
    assert jobs[0] is not None
    assert jobs[0].command.split()[0] == path
