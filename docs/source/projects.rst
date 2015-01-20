.. _projects:

========
Projects
========

GRAPE pipelines can be organized in projects. A project is a dedicated folder that contains all the project data including:

- the reference genome(s) and annotation(s)
- raw data
- analyses results

How to create a project
=======================

The grape command allows to create projects from the command line with a single init command:

.. code-block:: bash

    $ grape init

that creates a grape project in the current folder. In addition, a path to another folder can be specified:

.. code-block:: bash

    $ grape init /path/to/project

Project configuration
=====================

When a new project is initialized a default configuration file in Yaml format is created in the .grape folder. The default configuration can be seen using the grape config command and looks like the following:

.. code-block:: yaml

    project:
     date: 2015-01-13
     name: Default Project
     user: epalumbo
     genomes:
       human:
         male: /path/to/human/male
         female: /path/to/human/female
       mouse:
         male: /path/to/mouse/male
         female: /path/to/mouse/female

The following attributes are supported under the ``project`` configuration section:

===============  ================
 Name              Description
===============  ================
``name``         the project name
``desc``         a description of the project
``genomes``      the set of genomes used in the project
``annotations``  the set of annotations used in the projects
``date``         the creation date
``user``         the user that created the project
``group``        the group the user that created the project belongs to
===============  ================

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
