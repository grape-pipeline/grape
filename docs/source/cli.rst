.. _cli:

======================
Command line interface
======================

The ``config`` command can also be used to set or modify configuration values. For example, to add the path for a genome file we can use the following command:

.. code-block:: bash

    $ grape config genome /path/to/genome

In a similar way, we could also set a project property like the project name:

.. code-block:: bash

    $ grape config name MyProject

In case you need, it is possible to remove entries from the configuration file using the following command:

.. code-block:: bash

    $ grape config -d <key_name>
