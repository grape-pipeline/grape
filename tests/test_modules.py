import pytest
import os
from grape.buildout import module
from grape.grape import Grape
import jip

def test_module_decorator():
    if os.environ.get('GRAPE_HOME'):
        del os.environ['GRAPE_HOME']

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

    with pytest.raises(jip.ValidationError) as excinfo:
        jip.create_jobs(p)

    assert excinfo.value.message == 'GRAPE_HOME not defined. Please set the GRAPE_HOME environment variable!'

def test_module_decorator_with_grape_home():
    os.environ['GRAPE_HOME'] = os.getcwd() + '/test_data/home'

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

    path = j(Grape().home,'modules','gemtools','1.6.1','bin')

    jobs = jip.create_jobs(p, validate=False)

    assert len(jobs) == 1
    assert jobs[0] is not None
    assert jobs[0].env['PATH'].split(':')[0] == path

def test_module_decorator_with_grape_home_no_validate():
    os.environ['GRAPE_HOME'] = os.getcwd() + '/test_data/home'

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

        def get_command(self):
            return "bash", "gemtools index ${options()}"


    j = os.path.join

    p = jip.Pipeline()
    p.run('gemtools_test', input='genome.fa')

    path = j(Grape().home,'modules','gemtools','1.6.1','bin')

    jobs = jip.create_jobs(p, validate=False)

    assert len(jobs) == 1
    assert jobs[0] is not None
    assert jobs[0].env['PATH'].split(':')[0] == path

def test_module_decorator_pipeline_env():
    os.environ['GRAPE_HOME'] = os.getcwd() + '/test_data/home'

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

        def get_command(self):
            return "bash", "gemtools index ${options()}"

    @jip.tool('gemtools_test1')
    class gemtools1(object):
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

        def get_command(self):
            return "bash", "gemtools index ${options()}"

    @jip.pipeline('gt_pipeline_test')
    class testPipeline(object):
        """
        The GEM Indexer tool

        Usage:
            gt_pipeline -i <genome> [-o <genome_index>] [-t <threads>] [--no-hash]

        Options:
            --help  Show this help message
            -o, --output <genome_index>  The output GEM index file [default: ${input|ext}.gem]
            -t, --threads <threads>  The number of execution threads [default: 1]
            --no-hash  Do not produce the hash file [default: false]

        Inputs:
            -i, --input <genome>  The fasta file for the genome
        """
        def pipeline(self):
            p = jip.Pipeline()
            a = p.run('gemtools_test', input='genome.fa')
            b = p.run('gemtools_test1', input='genome.fa')
            return p

    j = os.path.join

    p = jip.Pipeline()
    p.run('gt_pipeline_test', input='genome.fa')

    path = j(Grape().home,'modules','gemtools','1.6.1','bin')

    jobs = jip.create_jobs(p, validate=False)

    assert len(jobs) == 2
    assert jobs[0] is not None
    assert jobs[0].env['PATH'].split(':')[0] == path

    assert jobs[1] is not None
    assert jobs[1].env['PATH'].split(':')[0] == path
