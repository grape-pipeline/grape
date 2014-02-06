from grape.grape import Project
from grape.grapeindex import GrapeDataset as Dataset
from grape.grapeindex import GrapeIndex as Index

import os
import pytest

def test_index():
    i = Index()
    i.insert(id='test', type='fastq', path='/data/fastq/test_1.fq')
    assert len(i.datasets['test'].fastq) == 1
    del i
    i = Index()
    i.format = {'fileinfo': ['type','path']}
    i.insert(id='test', type='fastq', path='/data/fastq/test_1.fq')
    print vars(i.datasets['test'])
    with pytest.raises(AttributeError):
        i.datasets['test'].type
    i.datasets['test'].primary == '/data/fastq/test_1.fq'


