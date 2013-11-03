Grape 2.0
=========

Development setup
-----------------
Please use virtualenv to develop in grape.  This is what you would usually do to prepare
your virtualenv environment:

  virtualenv --no-site-packages .
  source bin/activate

You might also want to take a look at the virtualenvwrapper.

We assume you have a dedicated virtualenv set up and activated. To get started:

    pip install -r requirements.txt

This will install all dependencies. In order to get the commands into path and
be able to run things from command line even if you are in development mode, do

    make devel

Documentation
-------------

Run 

  make docs

Then open

  ./docs/build/html/index.html

To see further instructions on how to use Grape.
