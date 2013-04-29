#!/usr/bin/env python
#
# Test grape Datasets
#

from grape import Dataset


def test_secondary_matching():
    print Dataset.find_secondary("test_0.fastq")
    assert Dataset.find_secondary("test_1.fastq.gz") == "test_2.fastq.gz"
    assert Dataset.find_secondary("test_0.fastq.gz") == "test_1.fastq.gz"
    assert Dataset.find_secondary("test_0.fastq") == "test_1.fastq"
    assert Dataset.find_secondary("test_0.fq") == "test_1.fq"
    assert Dataset.find_secondary("test_0.fq.gz") == "test_1.fq.gz"
    assert Dataset.find_secondary("test-0.fq.gz") == "test-1.fq.gz"
    assert Dataset.find_secondary("test.0.fq.gz") == "test.1.fq.gz"


def test_dataset_construction_typed_folder():
    d = Dataset("/data/fastq/test_1.fq")
    assert d.primary == "/data/fastq/test_1.fq"
    assert d.secondary == "/data/fastq/test_2.fq"
    assert d.data_folder == "/data", d.data_folder
    assert d.name == "test"
    assert d.folder("mappings") == "/data/mappings"


def test_dataset_construction_untyped_folder():
    d = Dataset("/data/test_1.fq")
    assert d.primary == "/data/test_1.fq"
    assert d.secondary == "/data/test_2.fq"
    assert d.data_folder == "/data", d.data_folder
    assert d.name == "test"
    assert d.folder("mappings") == "/data"


def test_dataset_construction_sorted_by_file():
    d = Dataset("/data/test_2.fq")
    assert d.primary == "/data/test_1.fq"
    assert d.secondary == "/data/test_2.fq"
    assert d.data_folder == "/data", d.data_folder
    assert d.name == "test"
    assert d.folder("mappings") == "/data"