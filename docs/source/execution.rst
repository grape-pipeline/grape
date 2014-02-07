==================
Pipeline Execution
==================

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

To run the pipeline on a HPC cluster you need to configure the JIP. Please refer to the `JIP documentation`_ for more information about this topic. With a valid JIP cluster configuration the `grape submit` command can be used to run jobs on the cluster.

.. note::

    A specific JIP database file for each GRAPE project is used and can be found at `<project>/.grape/grape_jip.db`.


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
.. _JIP pipeline system: http://github.com/thasso/pyjip
.. _JIP documentation: http://pyjip.rtfd.org
