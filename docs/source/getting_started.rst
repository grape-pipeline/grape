---------------
Getting started
---------------

This tutorial covers all the necessary steps to setup and run the default GRAPE pipeline on the included test dataset.

Installation
------------

Execute the following commands to install GRAPE:

.. code-block:: bash

    $ mkdir grape2
    $ cd grape2
    # create an isolated python environment for GRAPE
    grape2 $ virtualenv --no-site-packages .
    # activate the virtual environment
    grape2 $ source bin/activate
    # install GRAPE
    grape2 $ pip install distribute==0.6.36 zc.buildout==2.1.0
    grape2 $ pip install grape-pipeline

.. _venv:

Activate the virtualenv
~~~~~~~~~~~~~~~~~~~~~~~

With the installation above you will need to activate the virtual environment each time you want to use GRAPE:

.. code-block:: bash

    $ cd grape2
    grape2 $ source bin/activate

Pipeline buildout
-----------------

Once GRAPE is succesfully installed you need to run `grape-buildout` to setup the pipeline home folder with the required configuration files and modules.

The pipeline home folder location must be defined with the `GRAPE_HOME` environment variable:

.. code-block:: bash

    grape2 $ mkdir pipeline
    grape2 $ export GRAPE_HOME=$PWD/pipeline
    grape2 $ grape-buildout

If everything goes well you should get the following output:

.. code-block:: bash

    Creating directory '/home/epalumbo/git/grape.ant/grape2/pipeline/bin'.
    Creating directory '/home/epalumbo/git/grape.ant/grape2/pipeline/parts'.
    Creating directory '/home/epalumbo/git/grape.ant/grape2/pipeline/eggs'.
    Creating directory '/home/epalumbo/git/grape.ant/grape2/pipeline/develop-eggs'.
    Getting distribution for 'hexagonit.recipe.download'.
    Got hexagonit.recipe.download 1.7.
    Installing gem.
    Downloading http://barnaserver.com/gemtools/releases/GEMTools-static-i3-1.6.2.tar.gz
    grape.install_module: Extracting module package to /home/epalumbo/git/grape.ant/grape2/pipeline/modules/gemtools/1.6.2
    Installing flux.
    Downloading http://sammeth.net/artifactory/barna/barna/barna.capacitor/1.2.4/flux-capacitor-1.2.4.tgz
    grape.install_module: Extracting module package to /home/epalumbo/git/grape.ant/grape2/pipeline/modules/flux/1.2.4
    Installing samtools.
    Downloading http://genome.crg.es/~epalumbo/grape/modules/samtools-0.1.19.tgz
    grape.install_module: Extracting module package to /home/epalumbo/git/grape.ant/grape2/pipeline/modules/samtools/0.1.19
    Installing crgtools.
    Downloading http://genome.crg.es/~epalumbo/grape/modules/crgtools-0.1.tgz
    grape.install_module: Extracting module package to /home/epalumbo/git/grape.ant/grape2/pipeline/modules/crgtools/0.1
    Installing testdata.
    Downloading http://genome.crg.es/~epalumbo/grape/testdata.tgz
    testdata: Extracting package to /home/epalumbo/git/grape.ant/grape2/pipeline
    Removing directory '/home/epalumbo/git/grape.ant/grape2/pipeline/bin'.
    Removing directory '/home/epalumbo/git/grape.ant/grape2/pipeline/develop-eggs'.
    Removing directory '/home/epalumbo/git/grape.ant/grape2/pipeline/eggs'.
    Removing directory '/home/epalumbo/git/grape.ant/grape2/pipeline/parts'.


Project
-------

To run the pipeline you will need to create a folder for the project and initalize it with the `grape init` command:

.. code-block:: bash

    grape2 $ mkdir project
    grape2 $ cd project
    project $ grape init
    Initializing project ... Done

A project has been created and initialized with an empty configuration. For further information about GRAPE projects please see :ref:`projects`

Reference files
~~~~~~~~~~~~~~~

The reference genome and annotation files for the project must be set with the `grape config` command:

.. code-block:: bash

    project $ grape config --set genome $GRAPE_HOME/testdata/genome/H.sapiens.genome.hg19.test.fa
    project $ grape config --set annotation $GRAPE_HOME/testdata/annotation/H.sapiens.EnsEMBL.55.test.gtf
    project $ grape config
    Project: 'Default project'
    ==========  =========================================
    genome      genomes/H.sapiens.genome.hg19.test.fa
    annotation  annotations/H.sapiens.EnsEMBL.55.test.gtf
    ==========  =========================================

Fastq files
~~~~~~~~~~~

To import the test RNA-seq data into the project you have to run the `grape scan` command:

.. code-block:: bash

    grape2 $ grape scan $GRAPE_HOME/testdata/reads
    Scanning <your grape home>/testdata/reads folder ... 4 fastq files found
    Checking known data ... 4 new files found
    Adding 'testB': <your grape home>/testdata/reads/testB_1.fastq.gz
    Adding 'testB':  /home/epalumbo/git/grape.ant/grape2/project/data/testB_1.fastq.gz
    Adding 'testB': <your grape home>/testdata/reads/testB_2.fastq.gz
    Adding 'testB':  /home/epalumbo/git/grape.ant/grape2/project/data/testB_2.fastq.gz
    Adding 'testA': <your grape home>/testdata/reads/testA_1.fastq.gz
    Adding 'testA':  /home/epalumbo/git/grape.ant/grape2/project/data/testA_1.fastq.gz
    Adding 'testA': <your grape home>/testdata/reads/testA_2.fastq.gz
    Adding 'testA':  /home/epalumbo/git/grape.ant/grape2/project/data/testA_2.fastq.gz

You can check that the files were correctly imported with the `grape list` command:

.. code-block:: bash

    grape2 $ grape list
    Project: 'Default project'
    2 datasets registered in project
    =====  ======================  =====
    id     path                    type
    =====  ======================  =====
    testA  reads/testA_2.fastq.gz  fastq
    testA  reads/testA_1.fastq.gz  fastq
    testB  reads/testB_1.fastq.gz  fastq
    testB  reads/testB_2.fastq.gz  fastq
    =====  ======================  =====


Running the pipeline
--------------------

You can run the pipeline for all the test files from within the project folder with the `grape run` command. Before actually running, you can perform a dry run::

    project $ grape run --dry

This command will show you the pipeline graph and commands for all the samples. For one sample (e.g. testA) you can do::

    project $ grape run testA --dry

To submit the pipeline to a HPC cluster environment replace the **run** command with the **submit** command. A dry run will also show you information about the jobs that will be submitted such as threads, memory, queue, etc..

For more information about running GRAPE please see :ref:`execution`.







