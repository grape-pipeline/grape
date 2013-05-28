from grape.grape import Project
from grape.index import Metadata, Dataset, Index

import os
import pytest

def test_metadata_instance():
    d = {'labExpId': "0001", 'sex': 'M', 'age': 50}
    m = Metadata(d)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.id
    assert m.labExpId == "0001"
    assert m.sex == "M"
    assert m.age == "50"

def test_metadata_parse():
    str = "labExpId=0001; sex=M; age=50;"
    m = Metadata.parse(str)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.id
    assert m.labExpId == '0001'
    assert m.sex == "M"
    assert m.age == "50"

def test_metadata_tags():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    print m.get_tags()
    assert m.get_tags() == str

def test_index_entry_instance():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    e = Dataset(m)
    assert e.id == m.labExpId
    assert vars(m) == vars(e.metadata)

def test_index_entry_file():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    e = Dataset(m)
    str1 = 'labExpId=0001; type=bam; size=100; md5=af54e41; view=Alignments; path=./file;'
    f = Metadata.parse(str1)
    with pytest.raises(AttributeError):
        e.bam
    e.add_file(f.path, f)
    assert e.bam
    for k in ['type', 'size', 'md5', 'view', 'path']:
        assert getattr(e.bam[0], k) == getattr(f, k)

def test_index():
    p = Project('test_data/project_index')
    i = p.index
    assert len(i.datasets) == 1
    for d in i.datasets.values():
        assert len(d.fastq) == 2
        assert d.fastq[0].path == './data/test_1.fastq.gz'
        assert d.primary == './data/test_1.fastq.gz'

#def test_import():
#    p = Project('test_data/project_index')
#    i = p.data_index


