--------
Tutorial
--------

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

A project has been created and initialized with an empty configuration. For further information about projects please see :ref:`projects`

Reference files
~~~~~~~~~~~~~~~

The reference genome and annotation files for the project must be set with the `grape config` command:

.. code-block:: bash

        project $ grape config --set genome $GRAPE_HOME/testdata/genome/genome.fa
        project $ grape config --set annotation $GRAPE_HOME/testdata/annotation/annotation.gtf
        project $ grape config
        Project: 'Default project'
        ==========  =========================
        genome      genome/genome.fa
        annotation  annotation/annotation.gtf
        ==========  =========================

Fastq files
~~~~~~~~~~~
::
        quickstart $ grape setup

   or if you are on a cluster submit it::

        quickstart $ grape setup --submit
        Setting up Default Pipeline Setup
        (  1/2) | Submitted gem_index            806052
        (  2/2) | Submitted gem_t_index          806053

    check that the jobs complete::

        quickstart $ grape jobs --verbose
        Pipeline: Default Pipeline Setup
        gem_t_index   806053   Done
        gem_index     806052   Done


Running the pipeline
--------------------

If you already have the gem indices (genome and transcriptome) you can run the pipeline specifying the parameters on the command line::

     quickstart $ grape run -i ~/data/test_1.fastq.gz -g ~/data/genome_1Mbp.fa -a ~/data/annotation.gtf --quality 33 --read-type 2x76

If you followed the previous section to generate the indices you could run the pipeline as follows::

     quickstart $ grape run -i ~/data/test_1.fastq.gz -g genomes/genome_1Mbp.fa -a annotations/annotation.gtf --quality 33 --read-type 2x76

If you want to submit the pipeline to a HPC cluster environment replace the **run** command with the **submit** command.


For other use cases please see :ref:`execution`.







