.. _adminguide:

===========
Admin Guide
===========

Installation
============

The Grape environment has been deployed to Pypi to allow easy installation. To install Grape with this method do the following: 

.. code-block:: bash

    $ pip install grape

or

.. code-block:: bash
    
    $ easy_install grape

It is also possible to install Grape from the program git repository on GitHub. This should be done for development purposes or for having access to the latest development version of the program.

.. code-block:: bash
    
    $ git clone https://github.com/grape-pipeline/grape
    $ cd grape
    $ python setup.py install

Buildout and initialisation
===========================

After the basic setup is done, there will be a grape-buildout command available to the user. The command takes a path argument and triggers the buildout process on that path. This path is know as **grape_home** and should be made availabe to Grape by

- grape user config in $HOME/.grape
- GRAPE_HOME environment variable

The basic structure should be created::

    <grape_home>
      conf            -- configuration folder
        cluster.json  -- cluster configuration
        format.json   -- default index format configuration
        jobs.json     -- deafult jobs configuration
      modules         -- base directory for modules
        <name>        -- the module name
          <version>   -- the module version 
            activate  -- activate script to load the module into the current environment

The **grape_home** contains a global grape configuration directory and a set of modules. Each module must provide a name and a versions and can be activated by sourcing the activate script in the module folder. This will put the modules binaries in front of the path and prepend to any other environment variables as needed (i.e. PYTHONPATH).

Adding a new module to the buildout
===================================

In order to install a new module into the pipeline the buildout.conf file should be modified. A grape buildout configuration file looks like the following:

.. code-block:: ini

    [buildout]
    parts = gem
            flux
 
    [gem]
    recipe = grape:install_module
    url = http://barnaserver.com/gemtools/releases/GEMTools-static-i3-1.6.1.tar.gz
    md5sum = 6f660f2e57ded883ff1be4dc3e7ded51 
    name = gemtools
    version = 1.6.1
    
    [flux]
    recipe = grape:install_module
    url = http://sammeth.net/artifactory/barna/barna/barna.capacitor/1.2.3/flux-capacitor-1.2.3.tgz 
    md5sum = f62b001bbfda9d6ac6537f2f144509e7 
    name = flux
    version = 1.2.3

If a new part is required to be added, the new part should be added. As an example the fastqc programs are added to the buildout configuration:

.. code-block:: ini
    
    [fastqc]
    recipe = grape:install_module
    url = http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.10.1.zip
    md5sum = c93815ddfc0259bd58430e52ae4fb429
    name = fastqc
    version = 0.10.1

Then, to allow the [fastqc] part to be installed the part has to be added to the parts field in the [buildout] section:

.. code-block:: ini

    [buildout]
    parts = gem
            flux
            fastqc

After this giving the command:

.. code-block:: bash

    $ grape-buildout

would install the fastqc module, producing the following output:

.. code-block:: bash

    Installing gem.
    Skipping module gemtools-1.6.1 - already installed
    Installing flux.
    Skipping module flux-1.2.3 - already installed
    Installing fastqc.
    Downloading http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.10.1.zip
    fastqc: Extracting module package to /users/rg/epalumbo/grape-test/modules/fastqc/0.10.1

