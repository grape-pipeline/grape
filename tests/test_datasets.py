#!/usr/bin/env python
#
# Test grape Datasets
#

from grape.grapeindex import *

def test_dataset_init_dict():
    m = {'id': 'test'}
    d = GrapeDataset(**m)
    assert d.id == "test"
    d.add_file(**{'id':d.id, 'type':'fastq', 'path':'/data/fastq/test_1.fq'})
    assert d.primary == "/data/fastq/test_1.fq"
    #assert d.secondary == "/data/fastq/test_2.fq"
    assert d.secondary == None

def test_dataset_init():
    d = GrapeDataset(id='test')
    assert d.id == "test"
    d.add_file(id=d.id,type='fastq', path='/data/fastq/test_1.fq')
    assert d.primary == "/data/fastq/test_1.fq"
    #assert d.secondary == "/data/fastq/test_2.fq"
    assert d.secondary == None

def test_dataset_construction_typed_folder():
    d = GrapeDataset(id='test')
    assert d.id == "test"
    d.add_file(id=d.id,type='fastq', path='/data/fastq/test_1.fq')
    assert d.primary == "/data/fastq/test_1.fq"
    #assert d.secondary == "/data/fastq/test_2.fq"
    assert d.secondary == None


def test_dataset_construction_untyped_folder():
    d = GrapeDataset(id='test')
    assert d.id == "test"
    d.add_file(id=d.id,type='fastq', path='/data/test_1.fq')
    assert d.primary == "/data/test_1.fq"
    #assert d.secondary == "/data/test_2.fq"
    assert d.secondary == None

def test_dataset_construction_sorted_by_file():
    d = GrapeDataset(id='test')
    assert d.id == "test"
    d.add_file(id=d.id,type='fastq', path='/data/test_1.fq')
    assert d.primary == "/data/test_1.fq"
    #assert d.secondary == "/data/test_2.fq"
    assert d.secondary == None
