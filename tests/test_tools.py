#!/usr/bin/env python
#
# test basic tools
#
import jip, os
import grape.tools as tools

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
    assert jobs[1].configuration['output_prefix'].get() == j(ldir, 'gencode.gtf')
    assert jobs[1].configuration['max_length'].get() == '150'

    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_pipeline():
    p = jip.Pipeline()
    p.run('grape_gem_rnapipeline', fastq='reads_1.fastq.gz', index='index.gem', annotation='gencode.gtf')
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 2
    assert jobs[0].configuration['index'].get() == j(ldir, 'index.gem')
    assert jobs[0].configuration['fastq'].get() == j(ldir, 'reads_1.fastq.gz')
    assert jobs[0].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[0].configuration['quality'].get() == '33'
    assert jobs[0].configuration['output_dir'].get() == ldir
    assert jobs[0].configuration['name'].get() == 'reads'
    assert jobs[0].configuration['bam'].get() == j(ldir, 'reads.bam')
    assert jobs[0].configuration['bai'].get() == j(ldir, 'reads.bam.bai')
    assert jobs[0].configuration['map'].get() == j(ldir, 'reads.map.gz')

    assert jobs[1].configuration['input'].get() == j(ldir, 'reads.bam')
    assert jobs[1].configuration['name'].get() == 'reads'
    assert jobs[1].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[1].configuration['output_dir'].get() == ldir
    assert jobs[1].configuration['gtf'].get() == j(ldir, 'reads.gtf')

    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]


def test_gem_pipeline_with_output_dir():
    p = jip.Pipeline()
    p.run('grape_gem_rnapipeline', fastq='reads_1.fastq.gz', index='index.gem',
          annotation='gencode.gtf', output_dir="mydir")
    jobs = jip.create_jobs(p, validate=False)
    ldir = os.getcwd()
    j = os.path.join
    assert len(jobs) == 2
    assert jobs[0].configuration['index'].get() == j(ldir, 'index.gem')
    assert jobs[0].configuration['fastq'].get() == j(ldir, 'reads_1.fastq.gz')
    assert jobs[0].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[0].configuration['quality'].get() == '33'
    assert jobs[0].configuration['output_dir'].get() == "mydir"
    assert jobs[0].configuration['name'].get() == 'reads'
    assert jobs[0].configuration['bam'].get() == j(ldir, 'mydir/reads.bam')
    assert jobs[0].configuration['bai'].get() == j(ldir, 'mydir/reads.bam.bai')
    assert jobs[0].configuration['map'].get() == j(ldir, 'mydir/reads.map.gz')

    assert jobs[1].configuration['input'].get() == j(ldir, 'mydir/reads.bam')
    assert jobs[1].configuration['name'].get() == 'reads'
    assert jobs[1].configuration['annotation'].get() == j(ldir, 'gencode.gtf')
    assert jobs[1].configuration['output_dir'].get() == "mydir"
    assert jobs[1].configuration['gtf'].get() == j(ldir, 'mydir/reads.gtf')

    assert len(jobs[0].children) == 1
    assert len(jobs[1].dependencies) == 1
    assert jobs[0].children[0] == jobs[1]