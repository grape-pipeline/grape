.. _execution:

==================
Pipeline Execution
==================

The pipeline excution is based on `Nextflow`_.

The main GRAPE workflow can be run with the ``grape run`` command and is composed by several processes generating the following files:

    - Fasta index
    - GEMtools_ genome index
    - GEMtools_ transcriptome index
    - GEMtools_ mappings (bam files)
    - Raw Signal (bigwig files)
    - Contigs (bed files)
    - FluxCapacitor_ isoform expression quantifications (gtf files)
    - Gene quantifications (based on FluxCapacitor_ quantifications) (gff files)


Execution on different conditions
=================================

The simple execution of the pipeline with no defined project is as follows:

.. code-block:: bash

    grape2 $ grape run --genome /path/to/genome --annotation /path/to/annotation --index /path/to/index

If you set up a project, configure the reference genome and annotation and imported some fastq files you can use the following commands:

.. code-block:: bash

    # run the whole project
    grape2 $ grape run

    # run only the male samples
    grape2 $ grape run sex=male

In case you configured multiple genome and annotation files:

.. code-block:: bash

    # run human samples
    grape2 $ grape run organism=human --refs human


.. Useful links
.. _GEMTools: http://github.com/gemtools/gemtools
.. _FluxCapacitor: http://sammeth.net/confluence/display/FLUX/Home
.. _SAMtools: http://samtools.sourceforge.net/
.. _BEDtools: https://github.com/arq5x/bedtools2
.. _Nextflow: http://www.nextflow.io
.. _Nextflow documentation: http://www.nextflow.io/docs/latest/
