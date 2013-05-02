#!/usr/bin/env python
"""The grape main module"""
import os
import errno
import re
import json
from grape.index import Index

__version__ = "2.0-alpha.1"


class GrapeError(Exception):
    """Base grape error"""
    pass


class Grape(object):
    """Grape main class to run and submit pipelines"""

    def __init__(self):
        """"""
        self.home = os.getenv("GRAPE_HOME", None)
        self._default_job_config = None
        self._user_job_config = None

    def configure_job(self, tool, project, dataset, user_config=None):
        """Apply job configuration to this tool. The configuration
        is loaded first from the grape_home, then from the user home.
        Lastly, if specified, the user_config is applied to the job.

        In addition to the job configuration, grape specific attributes are
        set. This includes:

        - the log directory where the jobs log file is stored
        """
        if self._default_job_config is None:
            self._default_job_config = self.__load_configuration("jobs.json",
                                                                 use_global=True)
        if self._user_job_config is None:
            self._user_job_config = self.__load_configuration("jobs.json",
                                                                 use_global=False)

        self.__apply_job_config(tool, self._default_job_config.get("default",
                                                                   None))
        self.__apply_job_config(tool, self._default_job_config.get(tool._name,
                                                                   None))
        self.__apply_job_config(tool, self._user_job_config.get("default",
                                                                   None))
        self.__apply_job_config(tool, self._user_job_config.get(tool._name,
                                                                   None))

        if user_config is not None:
            self.__apply_job_config(tool, user_config)

        # set the log file location
        tool.job.logdir = project.logdir()


    def __apply_job_config(self, tool, cfg):
        if cfg is None:
            return
        for k, v in cfg.items():
            if hasattr(tool.job, k) and v is not None:
                tool.job.__setattr__(k, v)

    def get_cluster(self):
        """Return the cluster instance from either global or user
        configuration. Raises a GrapeError if no cluster is configured or the
        cluster implementation could not be loaded.
        """
        cluster = None
        cfg = self.__load_configuration("cluster.json", use_global=False)
        if len(cfg) == 0:
            cfg = self.__load_configuration("cluster.json", use_global=True)
        if len(cfg) == 0:
            raise GrapeError("No cluster configuration found!")

        class_name = cfg.get("class", None)
        if class_name is None:
            raise GrapeError("No cluster class specified!")
        del cfg["class"]
        # load the class

        try:
            components = class_name.split('.')
            module_name = ".".join(components[:-1])
            mod = __import__(module_name)
            for m in components[1:]:
                mod = getattr(mod, m)
            cluster = mod(**cfg)
        except Exception, e:
            raise GrapeError("Error while loading cluster implementation: "
                             "%s" % (str(e)))
        return cluster

    def __load_configuration(self, name, use_global=True):
        """Load a configuration file and return its content as a dictionary.
        If use_global is True, this searches for the file in the grape_home
        conf directory, otherwise it checks for the users .grape folder.

        An empty dict is returned if the requested configuration file does not
        exist.

        :param name: the name of the configuration file relative to the conf
            directory.
        :param use_global: set to False to search users $HOME/.grape folder
        """
        base = os.path.join(self.home, "conf")
        if not use_global:
            base = os.path.join(os.path.expanduser("~"), ".grape")

        conf_file = os.path.join(base, name)
        if not os.path.exists(conf_file):
            return {}

        with open(conf_file, "r") as f:
            ret = json.load(f)
            res = {}
            for k, v in ret.items():
                if v is not None and v != "":
                    res[k] = v
            return res


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

        if project:
            self.index_entry = project.data_index.entries[self.name]
        self.single_end = False  # todo: add single end detection and support
        self.quality = 33  # todo: add quality support

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

    def get_index(self):
        """Return the default index that should be used by this dataset
        """
        index = self.project.config.get('.'.join(['genomes', self.index_entry.metadata.sex, 'index']))
        if not index:
            index = self.project.get_indices()[0]
        return index


    def get_annotation(self):
        """Return the default annotation that should be used for this
        dataset
        """
        annotation = self.project.config.get('.'.join(['annotations', self.index_entry.metadata.sex, 'path']))
        if not annotation:
            annotation = self.project.get_annotations()[0]
        return annotation

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

    def __repr__(self):
        return "Dataset: %s" % (self.name)


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
        if self.exists():
            self.config = Config(self.path)
            self.data_index = Index()
            self.data_index.initialize()

    def initialize(self):
        """Initialize the current project.
        The initialization happens only if no .grape folder is found in the
        project path.
        """
        if self.exists():
            return
        # create .grape
        self.__mkdir(".grape")
        self.config = Config(self.path)
        self.data_index = Index()
        self.data_index.initialize()
        #create project structure
        self._initialize_structure()

    def logdir(self):
        """Get the path to the projects log file directory"""
        logdir_path = os.path.join(self.path, ".grape/logs")
        return logdir_path

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

    def get_indices(self):
        """Return the absolute path to all .gem files in the genomes
        folder of the project
        """
        folder = os.path.join(self.path, "genomes")
        return [os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.endswith(".gem")]

    def get_annotations(self):
        """Return the absolute path to all annotation files in the annotations
        folder of the project
        """
        folder = os.path.join(self.path, "annotations")
        return [os.path.join(folder, f)
                for f in os.listdir(folder) if (f.endswith(".gtf") or
                                                f.endswith(".gtf.gz"))]

    def get_datasets(self):
        """Return a list of all datasets found in this project"""
        data_folder = os.path.join(self.path, "data")
        datasets = {}
        # get the files in the data folder
        for f in Project.__search_fastq_files(data_folder):
            d = Dataset(f, project=self)
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
            elif not os.path.isfile(absname) and f == "fastq":
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

    def __init__(self, path):
        """Create a new configuration instance for a given project. If the
        project already has a configuration then load the existing information

        Parameter
        --------
        path - the path to the project
        """
        self.path = path
        self._config_file = os.path.join(path, '.grape/config')
        self.data = {}
        if os.path.exists(self._config_file):
            self._load_config()
        else:
            self._init_default_config()

    def _init_default_config(self):
        """Initialize a default configuration file for the current project
        """
        self.data['name'] = 'Default project'
        self.data['quality'] = '33'
        self.data['genomes'] = {'male': {}, 'female': {}}
        self.data['annotations'] = {'male': {}, 'female': {}}

        self._write_config()

    def _load_config(self):
        """Load the confguration information from the project config file
        """
        self.data = self._convert(json.load(open(self._config_file,'r')))

    def _write_config(self):
        """Write the configuration to the config file
        """
        with open(self._config_file,'w+') as config:
            json.dump(self.data, config, indent=4)


    def get_printable(self, tabs=4):
        """Return a the configuation information in a pretty printing layout

        Keyword arguments:
        ------------------
        tabs - indent size for printing
        """
        return json.dumps(self.data, indent=tabs)

    def remove(self, key, commit=False):# TODO: check empty fields when removing and remove them as well
        """Remove a key-value pair form the configuration

        Arguments:
        ----------
        key - the key to remove from the config

        Keyword arguments:
        ------------------
        commit - if True writes the changes to the configuration file. Default False
        """
        keys = key.split('.')

        d = self.data
        for k in keys:
            if isinstance(d, dict):
                if not k in d.keys():
                    raise GrapeError('Key %r does not exists' % k)
                if len(keys) > 1 and isinstance(d[k], dict):
                    d = d[k]

        del d[keys[-1]]

        if commit:
            self._write_config()

    def get(self, key):
        keys = key.split('.')

        d = self.data
        for k in keys:
            d = d[k]

        return d

    def set(self, key, value, commit=False):
        """Set values into the configuration for a given key

        Arguments:
        ----------
        key   -  the key of the configuration field
        value -  the value to add

        Keyword arguments:
        ------------------
        commit - if True writes the changes to the configuration file. Default False
        """

        keys = key.split('.')

        d = self.data
        for k in keys:
            if isinstance(d, dict):
                if not k in d.keys():
                    if keys.index(k) < len(keys)-1:
                        d[k] = {}
                    else:
                        d[k] = ''
                if isinstance(d[k], dict):
                    d = d[k]

        d[keys[-1]] = value

        if commit:
            self._write_config()

    def _convert(self, input):
        """Convert unicode input to utf-8

        Arguments:
        ----------
        input - the unicode input to convert
        """
        if isinstance(input, dict):
            ret = {}
            for k, v in input.iteritems():
                ret[self._convert(k)] = self._convert(v)
            return ret
        elif isinstance(input, list):
            return [self._convert(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
