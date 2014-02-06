----------
Quickstart
----------

To follow this guide you need to have the Grape environment already installed and configured in your system. For detailed information please see :ref:`Installation <adminguide>` and :ref:`User Guide <userguide>`.

What you need
-------------

- a couple of fastq files to be processed (single or paired end)
- a reference genome
- a reference annotation
- information about read quality and type (eg. fastq offset, protocol strandedness)

Setting up the pipeline
-----------------------

This step is performed to generate the gem indices needed for the pipeline run. If you already generated the GEM indices you can skip this step.

Procedure:

1.  create a project folder::
        
        [epalumbo@ant-login6 ~]$ mkdir quickstart

2.  move to the folder::

        [epalumbo@ant-login6 ~]$ cd quickstart

3. initialize the project::

        (grape.devel)[epalumbo@ant-login6 quickstart]$ grape init
        Initializing project ... Done
   
    A project will be created and initialized with an empty configuration.

4. Add genome and annotation to the project configuration::

        [epalumbo@ant-login6 quickstart]$ grape config --set genome ~/data/genome_1Mbp.fa 
        [epalumbo@ant-login6 quickstart]$ grape config --set annotation ~/data/annotation.gtf 
        [epalumbo@ant-login6 quickstart]$ grape config
        Project: 'Default project'
        ==========  ============================================================  
        genome      /nfs/users/rg/epalumbo/quickstart/genomes/genome_1Mbp.fa      
        annotation  /nfs/users/rg/epalumbo/quickstart/annotations/annotation.gtf  
        ==========  ============================================================

5. Run the setup pipeline::

        [epalumbo@ant-login6 quickstart]$ grape setup

   or if you are on a cluster submit it::

        [epalumbo@ant-login6 quickstart]$ grape setup --submit
        Setting up Default Pipeline Setup
        (  1/2) | Submitted gem_index            806052
        (  2/2) | Submitted gem_t_index          806053

    check that the jobs complete::

        [epalumbo@ant-login6 quickstart]$ grape jobs --verbose
        Pipeline: Default Pipeline Setup
        gem_t_index   806053   Done 
        gem_index     806052   Done


Running the pipeline
--------------------

If you already have the gem indices (genome and transcriptome) you can run the pipeline specifying the parameters on the command line::

     [epalumbo@ant-login6 quickstart]$ grape run -i ~/data/test_1.fastq.gz -g ~/data/genome_1Mbp.fa -a ~/data/annotation.gtf --quality 33 --read-type 2x76

If you followed the previous section to generate the indices you could run the pipeline as follows::

     [epalumbo@ant-login6 quickstart]$ grape run -i ~/data/test_1.fastq.gz -g genomes/genome_1Mbp.fa -a annotations/annotation.gtf --quality 33 --read-type 2x76

If you want to submit the pipeline to a HPC cluster environment replace the **run** command with the **submit** command.


For other use cases please see the :ref:`User Guide <userguide>`.
    



 


