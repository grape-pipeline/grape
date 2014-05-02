"""Test tools"""
import jip
import os
from grape.tools import gem, flux, rnaseqtools, bedtools, samtools

import pytest


def test_gem_setup_pipeline():
    p = jip.Pipeline()
    p.run('grape_gem_setup', input='genome.fa', annotation='gencode.gtf')
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 2
    assert jobs[0].configuration['input'].get() == j(ldir, 'genome.fa')
    assert jobs[0].configuration['output'].get() == j(ldir, 'genome.gem')
    assert jobs[0].configuration['no_hash'].get() == ''
    assert jobs[0].configuration['no_hash'].raw() is False

    assert jobs[1].configuration['index'].get() == j(ldir, 'genome.gem')
    assert jobs[1].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[1].configuration['max_length'].get() == '150'
    assert jobs[1].configuration['output_prefix'].get() == 'gencode.gtf'
    assert jobs[1].configuration['gem'].get() == j(ldir, 'gencode.gtf.junctions.gem')
    assert jobs[1].configuration['keys'].get() == j(ldir, 'gencode.gtf.junctions.keys')


    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_setup_pipeline_with_output_dir():
    p = jip.Pipeline()
    p.run('grape_gem_setup', input='genome.fa', annotation='gencode.gtf', output_dir="mydir")
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 2
    assert jobs[0].configuration['input'].get() == j(ldir, 'genome.fa')
    assert jobs[0].configuration['output'].get() == j(ldir, 'mydir/genome.gem')
    assert jobs[0].configuration['no_hash'].get() == ''
    assert jobs[0].configuration['no_hash'].raw() is False

    assert jobs[1].configuration['index'].get() == j(ldir, 'mydir/genome.gem')
    assert jobs[1].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[1].configuration['max_length'].get() == '150'
    assert jobs[1].configuration['output_prefix'].get() == 'mydir/gencode.gtf'
    assert jobs[1].configuration['gem'].get() == j(ldir, 'mydir/gencode.gtf.junctions.gem')
    assert jobs[1].configuration['keys'].get() == j(ldir, 'mydir/gencode.gtf.junctions.keys')


    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_filter_pipeline():
    p = jip.Pipeline()
    p.run('grape_gem_filter_pipeline', input="gem.map", max_mismatches="4",
          max_matches="10", name="test")
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 4
    assert jobs[0].configuration['input'].get() == j(ldir, 'gem.map')
    assert jobs[0].configuration['name'].get() == "test"
    assert jobs[1].configuration['max_levenshtein_error'].get() == "4"
    assert jobs[1].configuration['name'].get() == "test"
    assert jobs[2].configuration['max_matches'].get() == "10"
    assert jobs[2].configuration['name'].get() == "test"
    assert jobs[3].configuration['output'].get() == ''
    assert jobs[3].configuration['name'].get() == "test"

    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert len(jobs[2].dependencies) == 1
    assert len(jobs[3].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_pipeline():
    p = jip.Pipeline()
    p.run('grape_pipeline', fastq='reads_1.fastq.gz', genome='index.fa', annotation='gencode.gtf', max_matches='10', max_mismatches='4')
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 14
    print jobs
    assert jobs[2].configuration['index'].get() == j(ldir, 'index.gem')
    assert jobs[2].configuration['fastq'].get() == j(ldir, 'reads_1.fastq.gz')
    assert jobs[2].configuration['transcript_index'].get() == j(ldir, 'gencode.gtf.gem')
    assert jobs[2].configuration['quality'].get() == '33'
    assert jobs[2].configuration['output_dir'].get() == ldir
    assert jobs[2].configuration['name'].get() == 'reads'

    assert jobs[12].configuration['input'].get() == j(ldir, 'reads.bam')
    assert jobs[12].configuration['name'].get() == 'reads'
    assert jobs[12].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[12].configuration['output_dir'].get() == ldir
    assert jobs[12].configuration['output'].get() == j(ldir, 'reads.gtf')

    assert len(jobs[0].children) == 4
    assert len(jobs[1].dependencies) == 1
    assert len(jobs[2].dependencies) == 2
    assert len(jobs[3].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_pipeline_with_output_dir():
    p = jip.Pipeline()
    p.run('grape_pipeline', fastq='reads_1.fastq.gz', genome='index.fa',
          annotation='gencode.gtf', output_dir="mydir", max_matches='10', max_mismatches='4')
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 14
    assert jobs[2].configuration['index'].get() == j(ldir, 'index.gem')
    assert jobs[2].configuration['fastq'].get() == j(ldir, 'reads_1.fastq.gz')
    assert jobs[2].configuration['transcript_index'].get() == j(ldir, 'gencode.gtf.gem')
    assert jobs[2].configuration['quality'].get() == '33'
    assert jobs[2].configuration['output_dir'].get() == "mydir"
    assert jobs[2].configuration['name'].get() == 'reads'

    assert jobs[12].configuration['input'].get() == j(ldir, 'mydir/reads.bam')
    assert jobs[12].configuration['name'].get() == 'reads'
    assert jobs[12].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[12].configuration['output_dir'].get() == "mydir"
    assert jobs[12].configuration['output'].get() == j(ldir, 'mydir/reads.gtf')

    assert len(jobs[0].children) == 4
    assert len(jobs[1].dependencies) == 1
    assert len(jobs[2].dependencies) == 2
    assert len(jobs[3].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]
