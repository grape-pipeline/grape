.. _getting-started:

===============
Getting started
===============

This section shows all the necessary steps to setup and run the default GRAPE pipeline on the provided test dataset.


Installing
==========

GRAPE can be easily installed via ``pip`` with the following command:

.. code-block:: bash

    grape2 $ pip install grape-pipeline

To get the test data, software and configuration run the ``grape quickstart`` command. The command will create a ``quickstart`` folder under ``$GRAPE_HOME``. If ``$GRAPE_HOME`` is not defined ``$HOME/.grape`` will be used.

.. code-block:: bash

    grape2 $ export GRAPE_HOME=$PWD/pipeline
    grape2 $ grape quickstart

You can skip this step if you already have all the dependecies installed in the system.


Running
=======

Execute the following command to run the test pipeline on your local machine::

    grape2 $ grape run --genome /path/to/genome --annotation /path/to/annotation --index test-index.tsv

To submit the pipeline to a HPC cluster environment you need to work a bit with you GRAPE :ref:`configuration`.

For more information about running GRAPE please see :ref:`execution`.

.. Links
.. _EasyBuild: http://hpcugent.github.io/easybuild/
