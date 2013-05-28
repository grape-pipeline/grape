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


