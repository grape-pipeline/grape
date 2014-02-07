============
Installation
============

Grape can be installed like this:

.. code-block:: bash

    $ mkdir grape2
    $ cd grape2
    $ virtualenv --no-site-packages .
    $ source bin/activate
    $ pip install grape

If you are a developer, you can install from source as well:

.. code-block:: bash

    $ git clone https://github.com/grape-pipeline/grape
    $ cd grape
    $ virtualenv --no-site-packages .
    $ source bin/activate
    $ pip install -r requirements.txt
    $ python setup.py devel


Configuration and Modules
=========================

The Grape configuration and modules reside in a special folder, either

- in $HOME/.grape
- or in a folder specified by the GRAPE_HOME environment variable

For example::

    export GRAPE_HOME="/Users/maik/temp/grape-home"

This folder needs just one configuration file to get started::

    <grape_home>
      grape.conf      -- global configuration

You can leave this file empty for the moment.

Now let's install the modules. The grape-buildout command takes a path argument and and triggers the buildout process on that path.

.. code-block:: bash

    $ grape-buildout
    Installing gem.
    Skipping module gemtools-1.6.1 - already installed
    Installing flux.
    Skipping module flux-1.2.3 - already installed
    Installing fastqc.
    Downloading http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.10.1.zip
    fastqc: Extracting module package to /users/rg/epalumbo/grape-test/modules/fastqc/0.10.1

You will then see some modules appearing in grape_home::

    <grape_home>
      grape.conf      -- global configuration
      modules         -- base directory for modules
        <name>        -- the module name
          <version>   -- the module version
            activate  -- activate script to load the module into the current environment

