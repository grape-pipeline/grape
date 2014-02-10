============
Installation
============

Grape can be installed like this:

.. code-block:: bash

    $ mkdir grape2
    $ cd grape2
    grape2 $ virtualenv --no-site-packages .
    grape2 $ source bin/activate
    grape2 $ pip install distribute==0.6.36 zc.buildout==2.1.0
    # Since GRAPE 2.0 development is in beta stage you will need the --pre option
    grape2 $ pip install grape-pipeline --pre

If you are a developer, you can install from source as well:

.. code-block:: bash

    $ git clone https://github.com/grape-pipeline/grape
    $ cd grape
    $ make devel


Configuration and Modules
=========================

The Grape configuration and modules reside in a special folder, either

- in $HOME/.grape
- or in a folder specified by the GRAPE_HOME environment variable

For example::

    export GRAPE_HOME="/Users/maik/temp/grape-home"

To setup the pipeline just run the `grape-buildout` command. The command triggers the buildout process on the folder specified above.

.. code-block:: bash

    $ grape-buildout
    Creating directory '<grape_home>/bin'.
    Creating directory '<grape_home>/parts'.
    Creating directory '<grape_home>/eggs'.
    Creating directory '<grape_home>/develop-eggs'.
    Getting distribution for 'hexagonit.recipe.download'.
    Got hexagonit.recipe.download 1.7.
    Installing gem.
    Downloading http://barnaserver.com/gemtools/releases/GEMTools-static-i3-1.6.2.tar.gz
    grape.install_module: Extracting module package to <grape_home>/modules/gemtools/1.6.2
    Installing flux.
    Downloading http://sammeth.net/artifactory/barna/barna/barna.capacitor/1.2.4/flux-capacitor-1.2.4.tgz
    grape.install_module: Extracting module package to <grape_home>/modules/flux/1.2.4
    Installing samtools.
    Downloading http://genome.crg.es/~epalumbo/grape/modules/samtools-0.1.19.tgz
    grape.install_module: Extracting module package to <grape_home>/modules/samtools/0.1.19
    Installing crgtools.
    Downloading http://genome.crg.es/~epalumbo/grape/modules/crgtools-0.1.tgz
    grape.install_module: Extracting module package to <grape_home>/modules/crgtools/0.1
    Installing testdata.
    Downloading http://genome.crg.es/~epalumbo/grape/testdata.tgz
    testdata: Extracting package to <grape_home>
    Removing directory '<grape_home>/bin'.
    Removing directory '<grape_home>/develop-eggs'.
    Removing directory '<grape_home>/eggs'.
    Removing directory '<grape_home>/parts'.

After the buildout the following directories and files will be present in $GRAPE_HOME:

.. code-block:: bash

    <grape_home>/
    ├── conf
    ├── modules
    │   ├── crgtools
    │   │   └── 0.1
    │   │       └── bin
    │   │           ├── addXS
    │   │           ├── gem-2-sam
    │   │           ├── gt.filter
    │   │           ├── gt.quality
    │   │           └── pigz
    │   ├── flux
    │   │   └── 1.2.4
    │   │       ├── APACHE_LICENSE.txt
    │   │       ├── bin
    │   │       │   ├── flux-capacitor
    │   │       │   └── flux-capacitor.bat
    │   │       ├── LGPL_LICENSE.txt
    │   │       ├── lib
    │   │       │   ├── barna.capacitor-1.2.4.jar
    │   │       │   ├── barna.commons-1.22.jar
    │   │       │   ├── barna.io-1.22.jar
    │   │       │   ├── barna.lpsolver-1.22.jar
    │   │       │   ├── barna.model-1.22.jar
    │   │       │   ├── commons-cli-1.2.jar
    │   │       │   ├── commons-math-2.2.jar
    │   │       │   ├── dom4j-1.6.1.jar
    │   │       │   ├── groovy-all-1.8.4.jar
    │   │       │   ├── gson-2.1.jar
    │   │       │   ├── guava-r08.jar
    │   │       │   ├── itext-2.0.7.jar
    │   │       │   ├── javassist-3.12.1.GA.jar
    │   │       │   ├── jcommon-1.0.16.jar
    │   │       │   ├── jfreechart-1.0.13.jar
    │   │       │   ├── JRI-0.8-4.jar
    │   │       │   ├── jsap-2.1.jar
    │   │       │   ├── jtar-2.0.1.jar
    │   │       │   ├── reflections-0.9.5.jar
    │   │       │   ├── samtools-1.79.jar
    │   │       │   ├── slf4j-api-1.6.1.jar
    │   │       │   ├── slf4j-nop-1.6.1.jar
    │   │       │   ├── xml-apis-1.0.b2.jar
    │   │       │   ├── xpp3_min-1.1.3.4.O.jar
    │   │       │   └── xstream-1.2.2.jar
    │   │       ├── LICENSE
    │   │       └── README.txt
    │   ├── gemtools
    │   │   └── 1.6.2
    │   │       ├── bin
    │   │       │   ├── align_stats
    │   │       │   ├── compute-transcriptome
    │   │       │   ├── gem-2-gem
    │   │       │   ├── gem-2-sam
    │   │       │   ├── gem-2-wig
    │   │       │   ├── gem-indexer
    │   │       │   ├── gem-indexer_bwt-dna
    │   │       │   ├── gem-indexer_fasta2meta+cont
    │   │       │   ├── gem-indexer_generate
    │   │       │   ├── gem-info
    │   │       │   ├── gem-mappability
    │   │       │   ├── gem-mappability-retriever
    │   │       │   ├── gem-mapper
    │   │       │   ├── gem-retriever
    │   │       │   ├── gem-rna-mapper
    │   │       │   ├── gemtools
    │   │       │   ├── gt.construct
    │   │       │   ├── gtf-2-junctions
    │   │       │   ├── gt.filter
    │   │       │   ├── gt.mapset
    │   │       │   ├── gt.merge.map
    │   │       │   ├── gt.stats
    │   │       │   ├── splits-2-junctions
    │   │       │   └── transcriptome-2-genome
    │   │       ├── include
    │   │       │   ├── gem_tools.h
    │   │       │   ├── gt_alignment.h
    │   │       │   ├── gt_alignment_utils.h
    │   │       │   ├── gt_buffered_input_file.h
    │   │       │   ├── gt_buffered_output_file.h
    │   │       │   ├── gt_commons.h
    │   │       │   ├── gt_compact_dna_string.h
    │   │       │   ├── gt_counters_utils.h
    │   │       │   ├── gt_data_attributes.h
    │   │       │   ├── gt_dna_read.h
    │   │       │   ├── gt_dna_string.h
    │   │       │   ├── gt_error.h
    │   │       │   ├── gt_generic_printer.h
    │   │       │   ├── gt_hash.h
    │   │       │   ├── gt_ihash.h
    │   │       │   ├── gt_input_fasta_parser.h
    │   │       │   ├── gt_input_file.h
    │   │       │   ├── gt_input_generic_parser.h
    │   │       │   ├── gt_input_map_parser.h
    │   │       │   ├── gt_input_parser.h
    │   │       │   ├── gt_input_sam_parser.h
    │   │       │   ├── gt_map_align.h
    │   │       │   ├── gt_map.h
    │   │       │   ├── gt_map_score.h
    │   │       │   ├── gt_misms.h
    │   │       │   ├── gt_output_buffer.h
    │   │       │   ├── gt_output_fasta.h
    │   │       │   ├── gt_output_file.h
    │   │       │   ├── gt_output_map.h
    │   │       │   ├── gt_output_sam.h
    │   │       │   ├── gt_sequence_archive.h
    │   │       │   ├── gt_shash.h
    │   │       │   ├── gt_stats.h
    │   │       │   ├── gt_string.h
    │   │       │   ├── gt_template.h
    │   │       │   ├── gt_template_utils.h
    │   │       │   ├── gt_test.h
    │   │       │   └── gt_vector.h
    │   │       ├── lib -> lib64
    │   │       └── lib64
    │   │           └── libgemtools.a
    │   └── samtools
    │       └── 0.1.19
    │           ├── bin
    │           │   ├── ace2sam
    │           │   ├── bamcheck
    │           │   ├── bcftools
    │           │   ├── blast2sam.pl
    │           │   ├── bowtie2sam.pl
    │           │   ├── export2sam.pl
    │           │   ├── interpolate_sam.pl
    │           │   ├── maq2sam-long
    │           │   ├── maq2sam-short
    │           │   ├── md5fa
    │           │   ├── md5sum-lite
    │           │   ├── novo2sam.pl
    │           │   ├── plot-bamcheck
    │           │   ├── psl2sam.pl
    │           │   ├── r2plot.lua
    │           │   ├── sam2vcf.pl
    │           │   ├── samtools
    │           │   ├── samtools.pl
    │           │   ├── soap2sam.pl
    │           │   ├── varfilter.py
    │           │   ├── vcfutils.lua
    │           │   ├── vcfutils.pl
    │           │   ├── wgsim
    │           │   ├── wgsim_eval.pl
    │           │   └── zoom2sam.pl
    │           ├── examples
    │           │   ├── 00README.txt
    │           │   ├── bam2bed.c
    │           │   ├── calDepth.c
    │           │   ├── chk_indel.c
    │           │   ├── ex1.fa
    │           │   ├── ex1.sam.gz
    │           │   ├── Makefile
    │           │   ├── toy.fa
    │           │   └── toy.sam
    │           ├── include
    │           │   └── bam
    │           │       ├── bam2bcf.h
    │           │       ├── bam_endian.h
    │           │       ├── bam.h
    │           │       ├── bam_tview.h
    │           │       ├── bgzf.h
    │           │       ├── errmod.h
    │           │       ├── faidx.h
    │           │       ├── kaln.h
    │           │       ├── khash.h
    │           │       ├── klist.h
    │           │       ├── knetfile.h
    │           │       ├── kprobaln.h
    │           │       ├── kseq.h
    │           │       ├── ksort.h
    │           │       ├── kstring.h
    │           │       ├── razf.h
    │           │       ├── sam.h
    │           │       ├── sam_header.h
    │           │       └── sample.h
    │           ├── lib
    │           │   └── libbam.a
    │           └── man
    │               └── man1
    │                   └── samtools.1.gz
    └── testdata
        ├── annotation
        │   └── H.sapiens.EnsEMBL.55.test.gtf
        ├── genome
        │   └── H.sapiens.genome.hg19.test.fa
        └── reads
            ├── testA_1.fastq.gz
            ├── testA_2.fastq.gz
            ├── testB_1.fastq.gz
            └── testB_2.fastq.gz
