#!/usr/bin/env python
#
# Test project structure detection
#
from grape import Project


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


