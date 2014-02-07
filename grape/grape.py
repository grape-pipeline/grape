import os
import errno
import re
import json
from . import utils
#from indexfile.index import *
from grapeindex import GrapeIndex

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

    def configure_job(self, tool, project=None, dataset=None, user_config=None):
        """Apply job configuration to this tool. The configuration
        is loaded first from the grape_home, then from the user home.
        Lastly, if specified, the user_config is applied to the job.

        In addition to the job configuration, grape specific attributes are
        set. This includes:

        - the log directory where the jobs log file is stored
        """
        import jip

        job = tool
        name = None

        try:
            job = tool.job
            name = tool.name
        except:
            pass

        # load configuration lazily once
        if self._default_job_config is None:
            self._default_job_config = self.__load_configuration("jobs.json",
                                                                 use_global=True)
        if self._user_job_config is None:
            self._user_job_config = self.__load_configuration("jobs.json",
                                                              use_global=False)

        # apply configuration in order
        #
        # 0. hardocoded configuration for all jobs
        job.verbose = False

        # 1. set the log file location if a project is specified. This can be overwritten by
        # custom configuration
        if project is not None:
            job.logdir = project.logdir()

        # 2. the global default
        self.__apply_job_config(job, self._default_job_config.get("default",
                                                                   None))

        # 3. the global configuration for the tool based on the tool name
        self.__apply_job_config(job, self._default_job_config.get(name,
                                                                   None))

        # 4. the user default
        self.__apply_job_config(job, self._user_job_config.get("default",
                                                                None))
        # 5. the user configuration for the tool based on the tool name
        self.__apply_job_config(job, self._user_job_config.get(name,
                                                                None))
        # 6. user specified overrides
        if user_config is not None:
            self.__apply_job_config(job, user_config)

    def __apply_job_config(self, job, cfg):
        if cfg is None:
            return
        for k, v in cfg.items():
            if hasattr(job, k) and v is not None:
                job.__setattr__(k, v)

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
        if self.home is None:
            return {}

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
        self.genome_folder = "genomes"
        self.annotation_folder =  "annotations"
        self.data_folder = "data"
        if self.exists():
            self.config = Config(self.path)
            self.index = GrapeIndex(self.indexfile)

    def initialize(self, init_structure=True, folder_structure=''):
        """Initialize the current project.
        The initialization happens only if no .grape folder is found in the
        project path.

        :param init_structure: Initialize the project structure
        """
        if self.exists():
            return
        # create .grape
        self.__mkdir(".grape")
        self.config = Config(self.path)
        self.index = GrapeIndex(self.indexfile)
        if init_structure:
            if folder_structure:
                self.config.set('_folders', folder_structure)
                self.config._write_config()
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

    def load(self, path=None, format=None):
        """Load project from file.

        :param path: the indexfile to be loaded. If no path is passed the project index
                        is loaded
        :param format: the format of the index. It can be a path to a json file or a valid
                        json string containing format information
        """
        if not path:
            path = self.indexfile
        if not format and os.path.exists(self.formatfile):
            format = self.formatfile

        if format:
            self.index.set_format(format)

        self.index.open(path)

        if path != self.indexfile:
            self.index.path = self.indexfile

    def save(self, path=None, reload=False):
        """Save the project.

        :param path: the path of the output file. If no path is passed the
                        project index is used.
        """
        if not path:
            path = self.indexfile
        self.index.save(path)
        if reload:
            self.load(path)

    def export(self, out, type='index'):
        """Export the project.

        :param path: the path of the output file. If no path is passed the
                        stdout is used.
        """
        for line in self.index.export(type=type):
            out.write('%s%s' % (line,os.linesep))

    def add_dataset(self, path, id, file, file_info, link=True, compute_stats=False, update=False, absolute=False):
        file_info['id'] = id
        if link and path != os.path.join(self.path,self.data_folder):
            dest_folder = self.folder('fastq', id)
            # Creating link
            Project._make_link(file, dest_folder)
            if not absolute:
                dest_folder = os.path.basename(dest_folder)
            file = os.path.join(dest_folder,os.path.basename(file))
        file_info['path'] = file
        if compute_stats:
            # Computing file statistcs
            md5,size = utils.file_stats(file)
            file_info['md5'] = md5
            file_info['size'] = size
        print "Adding %r: " % (id), file
        self.index.insert(update=update, **file_info)

    @property
    def jip_db(self):
        jip_db_file = self.config.get('jip.db')
        if not jip_db_file:
            jip_db_file = os.path.join(self.path, '.grape', 'grape_jp.db')
        return jip_db_file

    @property
    def formatfile(self):
        """Return the path to the json file describing the format for the project index
        """
        format_file = os.path.join(self.path, '.grape','format.json')
        return format_file

    @property
    def indexfile(self):
        """Return the path to the index file for this project
        """
        indexfile = os.path.join(self.path,'.index')
        return indexfile

    @property
    def type_folders(self):
        if not self.config.get('_folders'):
            return False
        return self.config.get('_folders') == 'type'

    @property
    def dataset_folders(self):
        if not self.config.get('_folders'):
            return False
        return self.config.get('_folders') == 'dataset'


    def folder(self, name, dataset=None):
        """Resolve a folder based on datasets project folder and
        if type_folders. If type folders is True, this always resolves
        to the data folder. Otherwise, if name is specified, it resolves
        to the named folder under this datasets data folder.
        """
        if self.type_folders:
            return os.path.join(self.path, self.data_folder, name)
        if self.dataset_folders and dataset:
            return os.path.join(self.path, self.data_folder, dataset)

        return os.path.join(self.path, self.data_folder)


    def _initialize_structure(self):
        """Initialize the project structure"""

        self.__mkdir(self.annotation_folder)
        self.__mkdir(self.genome_folder)
        self.__mkdir(self.data_folder)
        if self.type_folders:
            self.__mkdir(os.path.join(self.data_folder,"fastq"))

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

    @staticmethod
    def _make_link(src_path, dest, symbolic=True):

        if not os.path.exists(src_path):
            raise GrapeError("The file %s does not exists" % (src_path))

        if not os.path.exists(dest):
            os.makedirs(dest)

        file_name = os.path.basename(src_path)
        dir_name = os.path.basename(os.path.dirname(src_path))

        dst_path = os.path.join('.', dest)

        if dir_name == 'fastq':
            dst_path = os.path.join(dst_path, dir_name)
        dst_path = os.path.join(dst_path, file_name)

        src_path = os.path.abspath(src_path)

        if os.path.abspath(dst_path) == src_path:
            return src_path

        if os.path.exists(dst_path) and os.path.islink(dst_path):
            os.unlink(dst_path)

        if symbolic:
            os.symlink(src_path, dst_path)
        else:
            try:
                os.link(src_path, dst_path)
            except OSError, e:
                if e.errno == errno.EXDEV:
                    os.symlink(src_path, dst_path)
                else:
                    # do not create the link and continue
                    pass

        return dst_path

    @staticmethod
    def _rm_link(path):
        if not os.path.exists(path):
            # the file does not exists
            return

        if os.path.islink(path):
            os.unlink(path)
        else:
            stat = os.stat(path)
            if stat.st_nlink > 1:
                # more than one copy - remove
                try:
                    os.remove(path)
                except OSError,e:
                    raise e
            else:
                # only one copy of the file - do not delete
                pass

    @staticmethod
    def _get_dest(path):
        name, ext  = os.path.splitext(path)
        genomes = set(['.fa','.fasta','.gem'])
        annotations = set(['.gtf','.gff'])
        data = set(['.fastq','.fastq.gz','.fq','.fq.gz'])
        if ext in genomes:
            return 'genomes'
        if ext in annotations:
            return 'annotations'
        if ext in data:
            return 'data'
        return None

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

    def get_datasets(self, **kwargs):
        """Return a list of datasets found in this project. Filters such as 'sex=M' can be used."""
        if not self.index.datasets:
            try:
                self.load()
            except:
                pass
        return self.index.select(**kwargs).datasets.values()

    @staticmethod
    def search_fastq_files(directory, level=0):
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
            #elif not os.path.isfile(absname) and f == "fastq":
            elif not os.path.isfile(absname):
                # scan folder
                sub = Project.search_fastq_files(absname,
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

        p = Project(path)

        if p.exists():
            return p
        else:
            path = os.path.dirname(path)
            if(path == "/"):
                return None
            return Project.find(path)

    @staticmethod
    def find_dataset(path):
        """Find dataset from path. Detect if paired and find mate
        file if possible

        path: path to the input file

        return:
            None if no dataset found
            [name, mate1] if single end
            [name, mate1, mate2] if paired end
        """

        basedir = os.path.dirname(path)
        name = os.path.basename(path)
        expr_paired = "^(?P<name>.*)(?P<delim>[_\.-])" \
               "(?P<id>\d)\.(?P<type>fastq|fq)(?P<compression>\.gz)*?$"
        expr_single = "^(?P<name>.*)\.(fastq|fq)(\.gz)*?$"
        match = re.match(expr_paired, name)
        if match:
            try:
                id = int(match.group('id'))
                if id < 2:
                    id += 1
                else:
                    id -= 1
                compr = match.group("compression")
                if compr is None:
                    compr = ""
                files = [path, os.path.join(basedir, "%s%s%d.%s%s")
                                                    % (match.group('name'),
                                                    match.group('delim'),
                                                    id, match.group('type'),
                                                    compr)]
                files.sort()

                return match.group('name'), files
            except:
                pass
        match = re.match(expr_single, name)
        if match:
            return match.group('name'), [path]
        return None

    def __str__(self):
        return "Project: %r" % (self.config.get("name"))


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
        self._stat_file = os.path.join(path, '.grape/stats')
        self.data = {}
        self.stats = {}
        if os.path.exists(self._config_file):
            self._load_config()
        else:
            self._init_default_config()

    def _init_default_config(self):
        """Initialize a default configuration file for the current project
        """

        import os, grp, pwd, json, datetime

        grape_home = os.environ.get("GRAPE_HOME")

        if grape_home:
            global_config = os.path.join(grape_home,'conf','stats.json')

            if os.path.exists(global_config):
                self.stats = json.load(open(global_config,'r'))

        self.data['name'] = 'Default project'
        self.stats['user'] = pwd.getpwuid(os.getuid()).pw_name
        if not self.data.get('group'):
            self.stats['group'] = grp.getgrgid(os.getgid()).gr_name
        self.stats['date'] = str(datetime.date.today())
        self.data['genome'] = ''
        self.data['index'] = ''
        self.data['annotation'] = ''
        self.data['quality'] = ''

        self._write_config()

    def _load_config(self):
        """Load the confguration information from the project config file
        """
        self.data = utils.uni_convert(json.load(open(self._config_file,'r')))
        self.stats = utils.uni_convert(json.load(open(self._stat_file,'r')))

    def _write_config(self, tabs=None):
        """Write the configuration to the config file
        """
        with open(self._config_file,'w+') as config:
            json.dump(self.data, config, indent=tabs)

        with open(self._stat_file,'w+') as config:
            json.dump(self.stats, config, indent=tabs)


    def get_printable(self, tabs=4):
        """Return the configuation information in json layout

        Keyword arguments:
        ------------------
        tabs - indent size for printing
        """
        return json.dumps(self.data, indent=tabs)

    def get(self, key):
        keys = key.split('.')

        d = self.data
        for k in keys:
            if not d.has_key(k):
                return None
            d = d[k]

        return d

    def get_values(self, key=None, exclude=[], sort_order=[], show_hidden=False, show_empty=False):
        """Return values from the data dictionary

        Keyword arguments:
        ------------------
        key - return values for a specific key
        exclude - exclude specified keys
        """
        data = self.data
        if key is not None:
             data = self.get(key)
        values = self._dot_keys(key, data, exclude)
        if not show_hidden:
            values = [(k,v) for k,v in values if not k.startswith('_')]
        if not show_empty:
            values = [(k,v) for k,v in values if v]
        if sort_order:
            values = self._get_sorted_values(values, sort_order)

        return values

    def _dot_keys(self, key, value, exclude):
        if value is None or type(value) is str:
            return [(key,value)]
        res = []
        for k,v in value.items():
            if k in exclude:
                continue
            if key:
                k = '.'.join([key,k])
            res.extend(self._dot_keys(k, v, exclude))
        return res

    def _get_sorted_values(self, values, sort_order):
        l = []
        for value in values:
            key = value[0].split('.')[0]
            if key in sort_order:
                l.append((sort_order.index(key),value))
            else:
                l.append((len(sort_order), value))
        l.sort()
        return [x[1] for x in l]

    def set(self, key, value, commit=False, make_link=True, dest=None, absolute=False):
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

        values = value.split(',')
        if len(values) == 1:
            values = values[0]

        if os.path.exists(values):
            if os.path.commonprefix([self.path, self.get(key)]) == self.path:
                self.remove(key)
            if make_link:
                # create symlink in project destination folder and replace path
                if not dest:
                    dest = Project._get_dest(values)
                symlink = Project._make_link(values, os.path.join(self.path, dest)
                                            if dest else self.path, symbolic=False)
                values = symlink
                if not absolute:
                    values = values.replace(self.path,"").lstrip("/")

        d[keys[-1]] = values

        if commit:
            self._write_config()

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
        for k in keys[:-1]:
            d = d[k]

        values = self.get_values(key=key)
        for k,v in values:
            if v.find(os.path.sep) > -1 and os.path.commonprefix([self.path, v]) == self.path:
                Project._rm_link(v)

        del d[keys[-1]]

        if commit:
            self._write_config()
