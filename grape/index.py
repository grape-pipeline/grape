"""The index module provides functionality around grape data indexing
"""
import re
import os
import json
import sys

from . import utils


class Metadata(object):
    """A class to store metadata retrieved from indices

    The keys of the tags are mapped to the Metadata class properties dinamically.
    The class properties name and values are derived form a dictionary
    passed as an argument to the contructor.
    """

    def __init__(self, kwargs):
        """Create an instance of a Metadata class

        Arguments:
        ----------
        kwargs - a dictionary containing name and values of the tags
        tags - a list of supported tags
        """
        for k,v in kwargs.items():
            self.__setattr__(k,str(v))

    def get_tags(self, tags=[], exclude=[], sep=' '):
        """Concatenate specified tags using the provided tag separator. The tag are formatted
        according to the 'index file' format

        Keyword arguments:
        -----------
        tags - list of keys identifying the tags to be concatenated. Default value is
               the empty list, which means that all tags will be returned.
        sep  - the tag separator character. The default value is a <space> according to
               the 'index file' format.
        """
        tag_list = []
        if not tags:
            tags = self.__dict__.keys()
        for key in tags:
            if key in exclude:
                continue
            tag_list.append(self.get_tag(key))
        return sep.join(tag_list)

    def get_tag(self, key, sep='=', trail=';'):
        """Return a key/value pair for a give tag, formatted according to the 'index file' format

        Arguments:
        -----------
        key   -  the key of the tag

        Keyword arguments:
        -------------------
        sep   -  the separator between key and value of the tag. Default is '='.
        trail -  trailing character of the tag. Default ';'.

        """
        value = self.__getattribute__(key)
        return sep.join([key, str(value)])+trail

    def extend(self, dict):
        for k,v in dict.items():
            self.__setattr__(k,v)

    #def __setattr__(self, name, value):
    #    if name in self.__dict__:
    #        raise ValueError("%r already contains %r property" % (self. __class__, key))
    #    self.__dict__[name] = str(value)

    @classmethod
    def parse(cls, string, info=[]):
        """Parse a string of concatenated tags and converts it to a Metadata object

        Arguments:
        ----------
        string - the concatenated tags
        """
        tags = cls._parse_tags(string)
        return Metadata(tags)

    @classmethod
    def _parse_tags(cls, str, sep='=', trail=';'):
        """Parse key/value pair tags from a string and returns a dictionary

        Arguments:
        ----------
        str - the tags string

        Keyword arguments:
        ------------------
        sep   -  the separator between key and value of the tag. Default is '='.
        trail -  trailing character of the tag. Default ';'.
        """
        tags = {}
        expr = '(?P<key>[^ ]+)%s(?P<value>[^%s]*)%s' % (sep, trail, trail)
        for match in re.finditer(expr, str):
            tags[match.group('key')] = match.group('value')
        return tags


class Dataset(object):
    """A class that represent dataset entry in the index file.

    Each entry is identified by the dataset name (eg. labExpId) and has metadata
    information as long as file information in order to be able to retrieve files
    and information related to the sample.
    """

    def __init__(self, metadata, id_key='labExpId', path_key='path'):
        """Create an instance of the IndexEntry class

        Arguments:
        ----------
        metadata -  an instance of :class:Metadata that contains the parsed metadata
                    information
        """
        self.metadata = Metadata({})
        for k,v in vars(metadata).items():
            if k not in ['type', 'view', 'md5', 'size', 'path']:
                self.metadata.__setattr__(k, v)
        self.tag_id = id_key
        if hasattr(metadata, path_key):
            self.add_file(metadata.__getattribute__(path_key), metadata)

    def add_file(self, path, meta):
        """Add the path of a file related to the dataset to the class files dictionary

        file_info - a :class:Metadata object containing the file information
        """
        file_info = Metadata({})
        for k,v in vars(meta).items():
            if k in ['type', 'view', 'md5', 'size', 'path']:
                file_info.__setattr__(k, v)
        type = file_info.type
        file_info.path = path
        if not hasattr(self, type):
            self.__setattr__(type, [])
        if not path in [x.path for x in self.__getattribute__(type)]:
            self.__getattribute__(type).append(file_info)
            self.__setattr__(type, sorted(self.__getattribute__(type), key=lambda file: file.path))
        else:
            flist = [x for x in self.__getattribute__(type) if x.path == path]
            if len(flist) > 1:
                raise ValueError('Duplicate index entry for %r' % path)
            self.__getattribute__(type)[self.__getattribute__(type).index(flist[0])] = file_info
        if type == 'fastq':
            self._get_fastq()

    def export(self, absolute=False, types=[]):
        """Convert an index entry object to its string representation in index file format
        """
        out = []
        if not types:
            types = [x for x in self.__dict__ if x not in ['metadata', 'type_folders', 'data_folder', 'tag_id']]
        for type in types:
            for file in self.__getattribute__(type):
                path = file.path
                if absolute:
                    path = os.path.abspath(path)
                tags = ' '.join([self.metadata.get_tags(),file.get_tags(exclude=['path', self.tag_id])])
                out.append('\t'.join([path, tags]))
        return out

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

    def get_genome(self, config):
        """Return the default index that should be used by this dataset
        """
        return config.get('.'.join(['genomes', self.sex, 'path']))

    def get_index(self, config):
        """Return the default index that should be used by this dataset
        """
        return config.get('.'.join(['genomes', self.sex, 'index']))

    def get_annotation(self, config):
        """Return the default annotation that should be used for this
        dataset
        """
        return config.get('.'.join(['annotations', self.sex, 'path']))

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

    def _get_fastq(self, sort_by_name=True):
        #self.primary = os.path.abspath(self.fastq[0].path)
        #self.secondary = None
        self.type_folders = False
        self.data_folder = os.path.dirname(self.primary)
        # check for type folders
        if os.path.split(self.data_folder)[1] == "fastq":
            self.type_folders = True
            self.data_folder = os.path.split(self.data_folder)[0]

        #detect secondary
        directory = os.path.dirname(self.primary)
        #self.secondary = Dataset.find_secondary(self.primary)
        #if self.secondary is not None:
        #    self.secondary = "%s/%s" % (directory, self.secondary)

        # set name
        #if self.secondary is not None:
        #    # exclude _1/_2 pair identifiers
        #    self.name = re.match("^(?P<name>.*)([_\.-])(\d)"
        #                         "\.(fastq|fq)(.gz)*?$",
        #                         os.path.basename(self.primary)).group("name")
        #else:
        #    # single datafile name
        #    self.name = re.match("^(?P<name>.*)\.(fastq|fq)(.gz)*?$",
        #                         os.path.basename(self.primary)).group("name")

        # sort primary and secondary
        if sort_by_name and len(self.fastq) > 1:
            s = sorted([self.fastq[0], self.fastq[1]], key = lambda x: x.path)
            self.fastq[0] = s[0]
            self.fastq[1] = s[1]

    def _get_single_end(self):
        return self.metadata.readType.find('2x') == -1

    def _get_quality(self):
        return self.metadata.quality

    def __getattr__(self, name):
        #if name is 'id':
        #    return self.metadata.__getattribute__(self.tag_id)
        if name not in ['metadata']:
            if hasattr(self.metadata, name):
                return self.metadata.__getattribute__(name)
            if name is 'id': return self.metadata.__getattribute__(self.tag_id)
            if name is 'primary': return self.fastq[0].path if hasattr(self,'fastq') and len(self.fastq) > 0 else None
            if name is 'secondary': return self.fastq[1].path if hasattr(self,'fastq') and len(self.fastq) > 1 else None
            if name is 'single_end': return self.metadata.readType.find('2x') == -1 if hasattr(self.metadata, 'readType') else False
        #if hasattr(self.metadata, name):
        #    return self.metadata.__getattribute__(name)
        raise AttributeError('%r object has no attribute %r' % (self.__class__.__name__,name))

    def __repr__(self):
        return "Dataset: %s" % (self.id)


class IndexDefinition(object):
    """A class to specify the index meta information
    """

    data = {}

##### TODO: not hardcode this information ##############################
    data['id'] = 'labExpId'
    data['metainfo'] = ['labProtocolId',
                'dataType',
                'age',
                'localization',
                'sraStudyAccession',
                'lab',
                'sex',
                'cell',
                'rnaExtract',
                'tissue',
                'sraSampleAccession',
                'readType',
                'donorId',
                'ethnicity'
                ]
    data['fileinfo'] = ['type',
                'size',
                'md5',
                'view'
                ]

    data['file_types'] = ['fastq', 'bam', 'bai', 'gff', 'map', 'bigWig', 'bed']

    data['default_path'] = '.index'
######################################################################

    @classmethod
    def dump(cls, tabs=2):
        return json.dumps(cls.data, indent=tabs)

class Index(object):
    """A class to access information stored into 'index files'.
    """

    def __init__(self, path, datasets={}, clear=False):
        """Creates an instance of an Index class

        path - path of the index file

        Keyword arguments:
        entries -  a list containing all the entries as dictionaries. Default empty list.
        """

        self.path = path
        self.datasets = datasets
        self._lock = None

        if not self.datasets:
            indices = path
            if not isinstance(indices, list):
                indices = [indices]
            for index in indices:
                if os.path.exists(index):
                    self.load(index, clear)

    def load(self, path, clear=False):
        """Add datasets to the index object by parsing an index file

        path -- path of the index file

        Keyword arguments:
        clear -- specify if index clean up is required before loadng (default False)
        """
        if clear:
            self.datasets = {}
        with open(os.path.abspath(path), 'r') as index_file:
            for line in index_file:
                self._parse_line(line)

    def save(self):
        """Save changes to the index file
        """
        with open(self.path,'w+') as index:
           self.export(out=index)


    def _parse_line(self, line):
        """Parse a line of the index file and append the parsed entry to the entries list.

        line - the line to be parsed
        """
        expr = '^(?P<file>.+)\t(?P<tags>.+)$'
        match = re.match(expr, line)
        file = match.group('file')
        tags = match.group('tags')

        meta = Metadata.parse(tags)
        dataset = self.datasets.get(meta.labExpId, None)

        if not dataset:
            dataset = Dataset(meta)
            self.datasets[dataset.id] = dataset

        dataset.add_file(file, meta)

    def add(self, id, path, file_info):
        meta = Metadata(file_info)
        dataset = self.datasets.get(id, None)
        if not dataset:
            raise ValueError("Dataset %r not found" % id)
        dataset.add_file(path, meta)


    def export(self, out=None, absolute=False):
        """Save changes made to the index structure loaded in memory to the index file
        """
        if not out:
            out = sys.stdout
        for dataset in self.datasets.values():
            for line in dataset.export(absolute=absolute):
                out.write('%s%s' % (line, os.linesep))


    def lock(self):
        """Lock the index"""
        if self._lock is not None:
            return False

        from lockfile import LockFile

        base = os.path.dirname(self.path)
        if not os.path.exists(base):
            os.makedirs(base)

        self._lock = LockFile(self.path)
        try:
            self._lock.acquire()
            return True
        except Exception, e:
            raise StoreException("Locking index file failed: %s" % str(e))

    def release(self):
        if self._lock is None:
            return False
        self._lock.release()
        self._lock = None
        return True

class _OnSuccessListener(object):
    def __init__(self, project, config):
        self.project = project
        self.config = config
    def __call__(self, tool, args):
        # grape.grape has an import grape.index.* so we
        # import implicitly here to avoid circular dependencies
        from .grape import Project

        project = Project(self.project)
        index = project.index
        try:
            index.lock()
            for k in tool.__dict__['outputs']:
                v = self.config[k]
                if os.path.exists(v):
                    info = {'type': k, 'md5': utils.md5sum(v)}
                    if self.config.has_key('view'):
                        info['view'] = self.config['view']
                    index.add(self.config['name'], v, info)
            index.save()
        finally:
            index.release()

def prepare_tool(tool, project, config):
    """Add listeners to the tool to ensure that it updates the job store
    during execution.

    :param tool: the tool instance
    :type tool: jip.tools.Tool
    :param project: the project
    :type project: grape.Project
    :param name: the run name used to identify the job store
    :type name: string
    """
    tool.on_success.append(_OnSuccessListener(project, config))

