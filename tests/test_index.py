from grape.index import Metadata, IndexEntry, Index

import os
import pytest

info = ['labExpId', 'sex', 'age']

def test_metadata_instance():
    d = {'labExpId': "0001", 'sex': 'M', 'age': 50}
    m = Metadata(info, d)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.labExpId
    assert m.id == "0001"
    assert m.sex == "M"
    assert m.age == "50"

def test_metadata_parse():
    str = "labExpId=0001; sex=M; age=50;"
    m = Metadata.parse(str)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.labExpId
    assert m.id == m.id
    assert m.sex == "M"
    assert m.age == "50"

def test_metadata_parse_info():
    str = "labExpId=0001; sex=M; age=50; tissue=Blood"
    m = Metadata.parse(str, info)
    assert len(m.__dict__.keys()) == 3
    with pytest.raises(AttributeError):
        m.labExpId
    assert m.id == "0001"
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
    str = "age=50; labExpId=0001; sex=M;"
    m = Metadata.parse(str)
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
    e = IndexEntry(m)
    assert e.id == m.id
    assert e.metadata == m

def test_index_entry_file():
    str = "labExpId=0001; age=50; sex=M;"
    m = Metadata.parse(str)
    e = IndexEntry(m)
    str1 = 'labExpId=0001; type=bam; size=100; md5=af54e41; view=Alignments'
    f = Metadata.parse(str1)
    assert len(e.files) == 0
    e.add_file(f)
    assert len(e.files) == 1
    assert e.files[f.type] == f

def test_index():
    path = '/users/rg/epalumbo/projects/BluePrint/bp_rna_dashboard_temp.crg.txt'
    i = Index(path)
    i.initialize()
    assert len(i.entries) == 47
    for entry in i.entries.values():
        assert len(entry.files) in [5, 6]