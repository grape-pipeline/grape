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

At the moment a Default Pipeline is configured, which includes the following modules:

- CRGtools, a set of in-house scripts and binaries from the *Computational Biology of RNA Processing* group at CRG Barcelona
- SAMtools_, utilities to manipulate sam files
- GEMTools_, utilities and pipelines for RNA-seq mapping
- FluxCapacitor_, a program for isoform quantification estimation

.. _GEMTools: http://github.com/gemtools/gemtools
.. _FluxCapacitor: http://sammeth.net/confluence/display/FLUX/Home
.. _SAMtools: http://samtools.sourceforge.net/

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

The pipeline excution relies on the `JIP pipeline system`_. It allows local execution and also provides HPC clusters integration.

The main GRAPE workflow can be run with the `grape run` command and is composed by two blocks:

    - pre-processing step to generate all the required input files for running the pipeline (one for all the samples in the project)
    - processing of the RNA-seq data (one for each samples)

The first block can also be run independently with the `grape run setup` command. The setup block check all the prerequisites for any configured pipeline and run all the necessary steps to reach a valid initial state from which the pipeline can be run. At present it consits of the following steps:

    - GEM genome index
    - GEM transcriptome index

In the second block the following steps are performed:

    - GEMtools RNA mapping pipeline run
    - GEMtools mappings filtering
    - isorform expression estimation with the Flux Capacitor

The pipeline can be run for a subset of the project dataset. Assuming that `foo` is a valid id for a sample you could run::

    $ grape run foo

to run the pipeline on the 'foo' sample data.

If you configured JIP for a compute cluster, the `grape submit` command can be used to run jobs on the cluster


.. _JIP pipeline system: https://github.com/thasso/pyjip
