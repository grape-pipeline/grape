#!/usr/bin/env python
"""The grape main module"""
import os
import errno

__version__ = "2.0-alpha.1"


class GrapeError(Exception):
    """Base grape error"""
    pass


class Project(object):
    """Base class for grape projects. A project hosts all the data
    relevant to a grape pipeline and provides basic functionallity around
    a project.

    The base class also provides a way to initialize and create a new project
    in a given folder.
    """

    def __init__(self, path):
        """Create a new project instance for a given path. The path
        must point to the projects root directory.

        Paramter
        --------
        path - path to the projects root folder where the .grape folder
               is located
        """
        self.path = path

    def initialize(self):
        """Initialize the current project.
        The initialization happens only if no .grape folder is found in the
        project path.
        """
        if self.exists():
            return
        # create .grape
        self.__mkdir(".grape")
        #create project structure
        self._initialize_structure()

    def exists(self):
        """Return true if the associated path is an initialized grape project
        """
        return os.path.exists("%s/.grape" % (self.path))

    def _initialize_structure(self):
        """Initialize the project structure"""
        self.__mkdir("annotations")
        self.__mkdir("genomes")
        self.__mkdir("data")

    def __mkdir(self, name):
        """Helper class to mimik mkdir -p """
        path = "%s/%s" % (self.path, name)
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise GrapeError("Unable to create folder %s" % (path))

