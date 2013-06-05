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
