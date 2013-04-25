#!/usr/bin/env python
"""The grape main module"""
import os
import errno
import re
import json

__version__ = "2.0-alpha.1"


class GrapeError(Exception):
    """Base grape error"""
    pass


class Grape(object):
    """Grape main class to run and submit pipelines"""

    def __init__(self):
        self.home = os.getenv("GRAPE_HOME", None)

    def run(self, project, datasets=None):
        """Run the pipeline for a given project. If no datasets are
        specified explicitly, run on all datasets.

        Parameter
        ---------
        project  - the project
        datasets - optional datasets
        """
        if datasets is None:
            datasets = project.get_datasets()


class Dataset(object):
    """A single dataset in a project
    """

    def __init__(self, primary, project=None, sort_by_name=True):
        """Initialize a dataset with a given project and a path to
        the main dataset file.

        Parameter
        ---------
        project - the project
        primary - the primary file
        """
        self.project = project
        self.primary = os.path.abspath(primary)
        self.secondary = None
        self.type_folders = False
        self.data_folder = os.path.dirname(self.primary)
        # check for type folders
        if os.path.split(self.data_folder)[1] == "fastq":
            self.type_folders = True
            self.data_folder = os.path.split(self.data_folder)[0]

        #detect secondary
        directory = os.path.dirname(self.primary)
        self.secondary = Dataset.find_secondary(self.primary)
        if self.secondary is not None:
            self.secondary = "%s/%s" % (directory, self.secondary)

        # set name
        if self.secondary is not None:
            # exclude _1/_2 pair identifiers
            self.name = re.match("^(?P<name>.*)([_\.-])(\d)"
                                 "\.(fastq|fq)(.gz)*?$",
                                 os.path.basename(self.primary)).group("name")
        else:
            # single datafile name
            self.name = re.match("^(?P<name>.*)\.(fastq|fq)(.gz)*?$",
                                 os.path.basename(self.primary)).group("name")

        # sort primary and secondary
        if sort_by_name and self.secondary is not None:
            s = sorted([self.primary, self.secondary])
            self.primary = s[0]
            self.secondary = s[1]

    def folder(self, name=None):
        """Resolve a folder based on datasets project folder and
        if type_folders. If type folders is True, this always resolves
        to the data folder. Otherwise, if name is specified, it resolves
        to the named folder under this datasets data folder.
        """
        if not self.type_folders or name is None:
            return self.data_folder
        else:
            return os.path.join(self.data_folder, name)

    @staticmethod
    def find_secondary(name):
        """Find secondary dataset file and return the basename of
        that file or return None
        """

        name = os.path.basename(name)
        expr = "^(?P<name>.*)(?P<delim>[_\.-])" \
               "(?P<id>\d)\.(?P<type>fastq|fq)(?P<compression>\.gz)*?$"
        match = re.match(expr, name)
        if match is not None:
            try:
                id = int(match.group("id"))
                if id < 2:
                    id += 1
                else:
                    id -= 1
                compr = match.group("compression")
                if compr is None:
                    compr = ""
                return "%s%s%d.%s%s" % (match.group("name"),
                                        match.group("delim"),
                                        id, match.group("type"),
                                        compr)
            except Exception:
                pass
        return None


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

    def get_datasets(self):
        """Return a list of all datasets found in this project"""
        data_folder = os.path.join(self.path, "data")
        datasets = {}
        # get the files in the data folder
        for f in Project.__search_fastq_files(data_folder):
            d = Dataset(f)
            if d.primary not in datasets:
                datasets[d.primary] = d

        return [d for k, d in datasets.items()]

    @staticmethod
    def __search_fastq_files(directory, level=0):
        """Search the given directory for fastq files and return them"""
        if directory is None or not os.path.exists(directory):
            return []
        if os.path.isfile(directory):
            return []

        datasets = []
        for f in os.listdir(directory):
            # add fastq files in
            absname = os.path.join(directory, f)
            is_file = os.path.isfile(absname)
            is_fastq = re.match(".*\.(fastq|fq)(\.gz)*?$", f)
            if is_file and is_fastq:
                datasets.append(absname)
            elif not os.path.isfile(absname) and level == 0 or f == "fastq":
                # scan folder
                sub = Project.__search_fastq_files(absname,
                                                   level=level + 1)
                datasets.extend(sub)
        return datasets

    @staticmethod
    def find(path=None):
        """Recursive search for a grape project folder starting at
        the given directory
        """
        if path is None:
            path = os.getcwd()

        if Project(path).exists():
            return Project(path)
        else:
            path = os.path.dirname(path)
            if(path == "/"):
                return None
            return Project.find(path)

class Config(object):
    """Base class for grape configuration. The configuration contains all the
    information related to a grape project.
    """

    def __init__(self, project):
        """Create a new configuration instance for a given project. If the
        project already has a configuration then load the existing information

        Parameter
        --------
        project - the project object
        """
        self.project = project
        self._config_file = os.path.join(project.path, '.grape/config')
        self.data = {}
        if os.path.exists(self._config_file):
            self._load_config()
        else:
            self._init_default_config()

    def _init_default_config(self):
        """Initialize a default configuration file for the current project
        """
        self.data['name'] = 'Default project'
        self.data['quality'] = 'offset33'
        self.data['genomes'] = {'male': '', 'female': ''}
        self.data['annotations'] = {'male': '', 'female': ''}

        with open(self._config_file, 'w+') as config:
              json.dump(self.data, config, indent=4)

    def _load_config(self):
        """Load the confguration information from the project config file
        """
        self.data = json.load(open(self._config_file,'r'))

    def get_printable(self, tabs=4):
        """Return a the configuation information in a pretty printing layout
        """
        return json.dumps(self.data, indent=tabs)


