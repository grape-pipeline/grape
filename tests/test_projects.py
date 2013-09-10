#!/usr/bin/env python
#
# Test project structure detection
#
from grape.grape import Project
from os.path import exists, join



def test_project_datasets_flat():
    p = Project("test_data/project_flat")
    datasets = p.get_datasets()
    assert len(datasets) == 1
    #assert len(datasets.fastq) == 2
    #first = filter(lambda x: x.name == "first", datasets)[0]
    #print first.primary
    #assert first.primary.endswith("first_1.fastq")
    #assert first.data_folder.endswith("project_flat/data")
    #print first.type_folders == False


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


def test_project_find_dataset():
    print Dataset.find_secondary("test_0.fastq")
    assert Dataset.find_secondary("test_1.fastq.gz") == ("test", "test_2.fastq.gz")
    assert Dataset.find_secondary("test_0.fastq.gz") == ("test","test_1.fastq.gz")
    assert Dataset.find_secondary("test_0.fastq") == ("test", "test_1.fastq")
    assert Dataset.find_secondary("test_0.fq") == ("test", "test_1.fq")
    assert Dataset.find_secondary("test_0.fq.gz") == ("test", "test_1.fq.gz")
    assert Dataset.find_secondary("test-0.fq.gz") == ("test", "test-1.fq.gz")
    assert Dataset.find_secondary("test.0.fq.gz") == ("test", "test.1.fq.gz")
