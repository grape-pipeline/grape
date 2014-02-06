from grape.grape import Config

import os
import pytest

def test_config_instance():
    config = Config('test_data/project_conf')
    assert config.data['name'] == 'test'
    assert config.data['quality'] == '33'
    assert config.data['organism'] == 'human'
    assert config.data['dataType'] == 'RNAseq'
    assert config.data['genomes'] == {'female': {'path': 'genomes/genome_AXM.fa'}, 'male': {'path': 'genomes/genome_AXYM.fa'}}
    assert config.data['annotations'] == {'female': {'path': 'annotations/anno_AXM.gtf'}, 'male': {'path': 'annotations/anno_AXYM.gtf'}}

def test_default_config():
    config = Config('test_data/project_default_conf')
    assert os.path.exists('test_data/project_default_conf/.grape/config')
    assert config.data['name'] == 'Default project'
    assert config.data['genome'] == ""
    assert config.data['annotation'] == ""
    os.remove('test_data/project_default_conf/.grape/config')

def test_get():
    config = Config('test_data/project_conf')
    assert config.get('name') == config.data['name']
    assert config.get('genomes.male.path') == config.data['genomes']['male']['path']

def test_modify():
    config = Config('test_data/project_conf')
    config.set('name', 'MyProject')
    assert config.get('name') == 'MyProject'
    config.set('genomes.male.path', 'genomes/genome.gem')
    assert config.get('genomes.male.path') == 'genomes/genome.gem'

def test_set_new():
    config = Config('test_data/project_default_conf')
    config.set('date', '01/01/1901')
    assert config.get('date') == '01/01/1901'
    config.set('datei.month', 'January')
    assert config.get('datei.month') == 'January'
    os.remove('test_data/project_default_conf/.grape/config')

def test_remove():
    config = Config('test_data/project_default_conf')
    config.remove('name')
    assert config.get('name') is None
    os.remove('test_data/project_default_conf/.grape/config')
