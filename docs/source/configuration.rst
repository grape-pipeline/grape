.. _configuration:

=============
Configuration
=============

GRAPE configuration is stored in a file called ``grape.yml`` located under the directory sepcified in ``$GRAPE_HOME`` (by default ``$HOME/.grape/``). The configuration includes the following sections:

- global: paths and global settings
- provisioning: settings for software used within the pipeline
- nextflow: common nextflow settings
- metastore: settings related to the indexfile and metadata formats

Nextflow
========

The nextflow sections contains common settings related to Nextflow. The following are supported:

- ``config``: a default configuration file for Nextflow is automatically created based on the general GRAPE configuration. If you want to use an external config file for the nextflow execution you can sepcify the path using this setting.
