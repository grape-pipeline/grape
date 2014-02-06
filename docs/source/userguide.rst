.. _userguide:

----------
User Guide
----------

--------------

==============
Grape Projects
==============

The main starting point to execute the pipeline is to create a grape project. A project has a dedicated folder that contains all the data for the project including:

- Data projects raw data
- All the results
- The reference genome/index
- The reference annotation

Create a project
================

The grape command allows to create projects from the command line with a single init command:

.. code-block:: bash

    $ grape init

This will create a grape project in the current folder. In addition, the path can be specified:

.. code-block:: bash

    $ grape init <path_to_project>

Project folder
--------------

The grape project folder consist of the following structure::

    .grape            -- the grape folder - this is where all the grape data goes
    annotation        -- genome annotations in gtf format and the transcriptome indices for the annotation 
    genome            -- index folder with genome indices. If there are multiple indices, they should follow the _AXYM suffix scheme (see below)
    data              -- input and result data folder

The genome indices should be suffixed with AXYM where:

- A - Autosome for all "numbered" chromosomes
- X - If the index contains the X chromosome
- Y - If the index contains the Y chromosome
- M - If the index contains Mitochondrial DNA

This is important as we will use this to distinguish between indices used for male/female if no further specification is given.

The data folder can be organised in various ways and the pipeline will detect the following scheme

- If the parent folder of a data file is called fastq, the pipeline will create subfolders for the results next to the fastq folder. Typically these will be mappings and quantification
- If nothing is detected the folder that contains the data file will also host the results

Project configuration
=====================

When a new project is initialized a default configuration file in Json format is created in the .grape folder. The default configuration can be see using the grape config command and looks like the following:

.. code-block:: json

    {
        "quality": "33", 
        "genome": "", 
        "name": "Default project", 
        "annotation": ""
    }
   
The grape config command can also be used to set or modify configuration values. For example, to add the path for a genome file we can use the following command:

.. code-block:: bash
    
    $ grape config --set genome <path_to_genome>

In a similar way, we could also set a project property like the project read quality offset:

.. code-block:: bash

    $ grape config --set quality 64

In case you need, it is possible to remove entries from the configuration file using the following command:

.. code-block:: bash

    $ grape config --remove <key_name>

Import datasets
===============

In order to import datasets into the project a csv/tsv file with all the meta information related to the datasets is needed. The file must have a header defining the datasets' properties used in it. Some properties are mandatory for the correct execution of the pipeline. The file must contain a dataset identifier to uniquely identify the sample and a path property to specify the fastq file path. Other properties like sex, quality, tissue, lab, etc. are optional and not strictly needed for the pipeline. execution. The default names for the compulsory properties are respectively **labExpId** and **path**. If different names are chosen for these properties the correspondence has to be specified in the grape import command. However, in general, the property names should comply with the ENCODE controlled vocabulary, please see :ref:`Index files <index-files>` for additional information.

The import command creates symlinks to the specified fastq files in the project data folder. It also creates an index file internal to the project, containing dataset entries for all the input and output files belonging to the project.

Following is an example of a valid csv file::

    path,labExpId,quality,sex,type,view
    ./data/test_1.fastq.gz,test,33,female,fastq,FqRd1
    ./data/test_2.fastq.gz,test,33,female,fastq,FqRd2

Note that the id and path properties have the default name. This file can be imported with the following command:

.. code-block:: bash

    $ grape import index.csv

In case one of the property names were different form the default (e.g **file_path** for the path property), the command would be like the following:

.. code-block:: bash

    $ grape import index.csv --path-key file_path
===============
Executing Grape
===============

The execution of the pipeline includes two main steps:

1. the setup step, in which all the prerequisites to run the pipeline are checked. If some files are missing the required tools are executed;
2. the execution step, which can be performed in two ways:
    - with the run command, that executes the pipeline for the given datasets on the machine from where the command has been invoked;
    - with the submit command, that executes the pipeline in a pre-configured HPC cluster in order to parallelize the execution.

Default Pipeline
================

At the moment a Default Pipeline is configured, which includes the following tools:

- the `GEMTools <http://github.com/gemtools/gemtools>`_ pipeline, for the mapping step
- the `FluxCapacitor <http://sammeth.net/confluence/display/FLUX/Home>`_ program, for the isoform quanitfication step

Setup
=====

The basic idea of the setup is to check all the prerequisites for any configured pipeline and run all the necessary steps to reach a valid initial state from which the pipeline can be run. Prerequisites here means all the common files and configurations needed to be able to run the pipeline on several datasets and that have to be created once.
At the moment the grape setup command executes the gemtools index and t-index commands to create the genome index and transcriptome index files needed to run the Default Pipeline:

.. code-block:: bash

    $ grape setup
    Setting up Default Pipeline
    (  1/2) | Running gem_index            : DONE [0:00:04]
    (  2/2) | Running gem_t_index          : DONE [0:00:02]

Execution
=========

The execution step run the pipeline on the given dataset(s). The pipeline can be run locally using the grape run command, int he following way:

.. code-block:: bash

    $ grape run
    Starting pipeline run: Default Pipeline test
    (  1/2) | Running gem                  : DONE [0:00:25]
    (  2/2) | Running flux                 : DONE [0:00:06]

If a cluster configuration is provided during the Grape installation, the grape submit command can be used to run jobs on the cluster. The job id of each submitted job will be reported in the standard output of the command:
    
.. code-block:: bash

    $ grape submit
    Submitting pipeline run: Default Pipeline test
    (  1/2) | Submitted gem                  780220
    (  2/2) | Submitted flux                 780221

Please see the Grape Jobs Management page to have an overview on the Grape features around Jobs management.
If some/all the output files for the pipeline are already present the related tool is skipped in the pipeline run/submission:

.. code-block:: bash
    
    $ grape run/submit
    Starting/Submitting pipeline run: Default Pipeline test
    (  1/2) | Skipped gem                  
    (  2/2) | Skipped flux
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
