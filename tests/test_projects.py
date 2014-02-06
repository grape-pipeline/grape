#!/usr/bin/env python
#
# Test project structure detection
#
from grape.grape import Project
from os.path import exists, join



def test_project_initialization_with_structure(tmpdir):
    p = Project(str(tmpdir))
    p.initialize()
    assert tmpdir.ensure("data", dir=True)
    assert tmpdir.ensure("annotation", dir=True)
    assert tmpdir.ensure("genomes", dir=True)
    assert tmpdir.ensure(".grape", dir=True)

def test_project_initialization_without_structure(tmpdir):
    p = Project(str(tmpdir))
    assert not exists(join(str(tmpdir), "data"))
    assert not exists(join(str(tmpdir), "annotation"))
    assert not exists(join(str(tmpdir), "genomes"))

    p.initialize(init_structure=False)
    assert not exists(join(str(tmpdir), "data"))
    assert not exists(join(str(tmpdir), "annotation"))
    assert not exists(join(str(tmpdir), "genomes"))
    assert tmpdir.ensure(".grape", dir=True)


def test_project_find_dataset_dataset():
    assert Project.find_dataset("test_1.fastq.gz") == ("test", ["test_1.fastq.gz", "test_2.fastq.gz"])
    assert Project.find_dataset("test_0.fastq.gz") == ("test", ["test_0.fastq.gz", "test_1.fastq.gz"])
    assert Project.find_dataset("test_0.fastq") == ("test", ["test_0.fastq", "test_1.fastq"])
    assert Project.find_dataset("test_0.fq") == ("test", ["test_0.fq", "test_1.fq"])
    assert Project.find_dataset("test_0.fq.gz") == ("test", ["test_0.fq.gz", "test_1.fq.gz"])
    assert Project.find_dataset("test-0.fq.gz") == ("test", ["test-0.fq.gz", "test-1.fq.gz"])
    assert Project.find_dataset("test.0.fq.gz") == ("test", ["test.0.fq.gz", "test.1.fq.gz"])