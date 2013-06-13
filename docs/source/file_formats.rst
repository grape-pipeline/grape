============
File formats
============

.. _index-files:

Index files
===========

Index files are used to store information related to files. Information can be metadata information about samples or any other properties about samples or raw files. The employed vocabulary is derived by the `ENCODE controlled vocabulary <http://genome.ucsc.edu/ENCODE/otherTerms.html>`_.

Specifications
--------------

The index file contains several lines with the following information::

    <path><TAB><tag_list>

where a tag_list is a <space> separated list of key/value pairs with the following format::

    <key>=<value>;
 
Example::

    /projects/project1/RNAseq/reads/sample_1.fastq.gz    dataType=RNASeq; donorId=000001; sraSampleAccession=ERS000001; ethnicity=NA; view=FastqRd1; size=17044595902; sraStudyAccession=ERP000001; labExpId=ERR000001; readType=2x76; tissue=Blood; age=65; lab=LAB; cell=K-562; localization=cell; type=fastq; rnaExtract=total; labProtocolId=000001; sex=M; md5sum=a6ec9f07891228dd25110be949f4cece;
    /projects/project1/RNAseq/reads/sample_2.fastq.gz    dataType=RNASeq; donorId=000001; sraSampleAccession=ERS000001; ethnicity=NA; view=FastqRd2; size=17044595902; sraStudyAccession=ERP000001; labExpId=ERR000001; readType=2x76; tissue=Blood; age=65; lab=LAB; cell=K-562; localization=cell; type=fastq; rnaExtract=total; labProtocolId=000001; sex=M; md5sum=a6ec9f07891228dd25110be949f4cece;

Project configuration files
===========================

Grape project configuration files are text files in `Json <http://www.json.org/>`_ format. The config file represent a dictionary for the project configuration. Any key/value pair can be specified, but at the moment only the following items are used n the pieline:

- **name**, the project name
- **quality**, a global quality offset for the reads
- **genome**, the genome to be used in the pipeline (please see details below)
- **annotation**, the annotation to be used in the pipeline (please see details below)
 
Following is a simple example of a configuration file:

.. code-block:: json

    {
        "name": "Test",
        "quality": "33", 
        "annotation": "annotations/annotation.gtf",      
        "genome": "genomes/genome_1Mbp.fa"
    }

Genome and annotation
---------------------

The genome and annotation items can be specified in different ways, depending on project/user needs. At the moment two modes are supported:

- the one above is the simplest, in which only one genome and one annotation are assumed to be used for the whole project;
- the second supported way is specifying different genome and annotation files depending on the sex of the samples. In that case, the example above would look like the following:

  .. code-block:: json

    {
        "name": "Test",
        "quality": "33",
        "annotations": {
            "male": {
                "path": "annotations/annotation.gtf"
            }
        },      
        "genomes": {
            "male": {
                "path": "genomes/genome_1Mbp.fa"
            }
        },     
    }

  In order to use this, the sex property for each dataset should be specified in the project index file. The key representing the sex in the configuration file must correspond to the value used to specify the sex in the index file. The path key is added here in case the user would like to specify additional information (e.g. the direct path to the genome index if already present). However, at the moment this additional information is ignored by the pipeline, if present.

Other more complex scenarios will be supported and are currently under development.
