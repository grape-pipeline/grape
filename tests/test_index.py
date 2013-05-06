from grape import Project
from grape.index import Metadata, IndexEntry, Index

import os
import pytest

info = ['labExpId', 'sex', 'age']

def test_metadata_instance():
    d = {'labExpId': "0001", 'sex': 'M', 'age': 50}
    m = Metadata(info, d)
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

def test_metadata_parse_info():
    str = "labExpId=0001; sex=M; age=50; tissue=Blood"
    m = Metadata.parse(str, info)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.id
    assert m.labExpId == "0001"
    assert m.sex == "M"
    assert m.age == "50"
    with pytest.raises(AttributeError):
        m.name

def test_metadata_get():
    str = "labExpId=0001; sex=M; age=50;"
    m = Metadata.parse(str)
    assert m.get('sex') == "M"
    with pytest.raises(ValueError):
        m.get('name')

def test_metadata_tags():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    print m.get_tags()
    assert m.get_tags() == str

def test_metadata_add_one():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    with pytest.raises(AttributeError):
        m.name
    m.add({'name': 'test'})
    m.name == 'test'
    m.add({'length': 100})
    m.length == "100"

def test_metadata_add():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    with pytest.raises(AttributeError):
        m.name
    m.add({'name': 'test', 'length': 100})
    m.name == 'test'
    m.length == "100"

def test_metadata_contains():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    assert m.contains('age')
    assert not m.contains('name')

def test_index_entry_instance():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    e = IndexEntry(m, {'metainfo': ['labExpId', 'age', 'sex'], 'id': 'labExpId'})
    assert e.id == m.labExpId
    assert e.metadata == m

def test_index_entry_file():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    e = IndexEntry(m, {'metainfo': ['labExpId', 'age', 'sex'], 'fileinfo': ['type', 'md5', 'size', 'view'], 'file_types': ['bam'], 'id': 'labExpId'})
    str1 = 'labExpId=0001; type=bam; size=100; md5=af54e41; view=Alignments; path=./file;'
    f = Metadata.parse(str1)
    assert len(e.files) == 0
    e.add_file(f)
    assert len(e.files) == 1
    assert e.files[f.type][0] == f

def test_index():
    p = Project('test_data/project_index')
    i = p.data_index
    assert len(i.entries) == 1
    for entry in i.entries.values():
        assert len(entry.files) == 1
        assert len(entry.files['fastq']) == 2
        assert entry.files['fastq'][0].path == './data/test_1.fastq.gz'

def test_import_tsv():
    path = 'test_data/test.tsv'
    i = Index(None)
    i.initialize(clear=True)
    i.import_sv(path)
    assert len(i.entries.values()) == 3
    #assert i.entries.keys() == ['1', '3', '2']
    #for k in ['1', '2', '3']:
    #    assert i.entries[k].id == k
    #i.entries['1'].metadata.get_tags() == "F1=a; F2=b; ID=1;\n"
    #i.entries['2'].metadata.get_tags() == "F1=c; F2=d; ID=2;\n"
    #i.entries['3'].metadata.get_tags() == "F1=e; F2=f; ID=3;\n"


def test_import_csv():
    path = 'test_data/test.csv'
    i = Index(None)
    i.initialize(clear=True)
    i.import_sv(path,sep=',')
    assert len(i.entries.values()) == 3
    #assert i.entries.keys() == ['1', '3', '2']
    #for k in ['1', '2', '3']:
    #    assert i.entries[k].id == k
    #i.entries['1'].metadata.get_tags() == "F1=a; F2=b; ID=1;\n"
    #i.entries['2'].metadata.get_tags() == "F1=c; F2=d; ID=2;\n"
    #i.entries['3'].metadata.get_tags() == "F1=e; F2=f; ID=3;\n"
