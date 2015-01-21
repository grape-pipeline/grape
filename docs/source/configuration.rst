.. _configuration:

=============
Configuration
=============

GRAPE configuration is stored in a file called ``grape.yml`` located under the directory sepcified in ``$GRAPE_HOME`` (by default ``$HOME/.grape/``). The configuration includes the following sections:

================  ==========================
``global``        paths and global settings
``provisioning``  settings for software used within the pipeline
``execution``     common nextflow settings
``index``         settings related to the indexfile and metadata formats
``project``       project setting
================  ==========================

Example
-------

.. code-block:: yaml

	global:
		home: /path/to/home

	provisioning:
		tool: modules

	execution:
		config: /path/to/config
		executor: local
		errorStrategy: ignore

	index:
		id: labExpId

	project:
		name: ENCODE


