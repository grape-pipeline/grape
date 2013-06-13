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
