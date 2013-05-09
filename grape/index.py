"""The index module provides functionality around grape data indexing
"""
import re
import os
import json
import sys
import grape.utils

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
            self.__setattr__(k,v)

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
        if not info:
            info = tags.keys()
        return Metadata(info, tags)

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

    def __init__(self, metadata, id_key):
        """Create an instance of the IndexEntry class

        Arguments:
        ----------
        metadata -  an instance of :class:Metadata that contains the parsed metadata
                    information
        """
        self.metadata = metadata
        self.tag_id = id_key
        self.id = self.metadata.__getattribute__(self.tag_id)
        self.single_end = self._get_single_end()  # todo: add single end detection and support
        self.quality = self._get_quality()  # todo: add quality support

    def add_file(self, file_info):
        """Add the path of a file related to the dataset to the class files dictionary

        Arguments:
        ----------
        file_info - a :class:Metadata object containing the file information
        """
        type = file_info.type
        if not hasattr(self, type):
            self.__setattr__(type, [])
        self.__getattribute__(type).append(file_info)
        self.__setattr__(type, sorted(self.__getattribute__(type), key=lambda file: file.path))
        if type == 'fastq':
            self._get_fastq()

    def export(self, absolute=False, types=[]):
        """Convert an index entry object to its string representation in index file format
        """
        out = []
        if not types:
            types = [x for x in self.__dict__ if x not in ['id', 'metadata', 'primary', 'secondary', 'type_folders', 'data_folder', 'tag_id', 'quality', 'single_end']]
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

    def _get_fastq(self, sort_by_name=True):
        self.primary = os.path.abspath(self.fastq[0].path)
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
        if sort_by_name and self.secondary is not None:
            s = sorted([self.primary, self.secondary])
            self.primary = s[0]
            self.secondary = s[1]

    def _get_single_end(self):
        return self.metadata.readType.find('2x') == -1

    def _get_quality(self):
        return self.metadata.quality

    def __repr__(self):
        return "Dataset: %s" % (self.id)


class IndexType(object):
    """A 'enum' like class for specifying index types. An index can have the following types:

    META - the index only stores metadata for the given datasets but no file information
    DATA - the index stores metadata, a file path and additional information related to the file
    """
    META = 0
    DATA = 1

    @classmethod
    def get(cls, str):
        return {
            'META': cls.META,
            'DATA': cls.DATA,
            cls.META: 'META',
            cls.DATA: 'DATA'
        }.get(str, None)

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

    def __init__(self, project, type=IndexType.DATA, entries={}, meta={}):
        """Creates an instance of an Index class

        Arguments:
        ----------
        path - path of the index file

        Keyword arguments:
        ------------------
        type    -  a :class:IndexType type. Default is DATA
        entries -  a list containing all the entries as dictionaries. Default empty list.
        """

        self.project = project
        self.type = type
        self.entries = entries
        self.meta = meta

        if project and project.has_metainf():
            self.__load_meta()


    def __load_meta(self):
        meta_file = self.project.metainf()
        with open(meta_file, 'r') as meta:
            self.meta = grape.utils.uni_convert(json.load(meta))

    def __export_meta(self, tabs=2):
        meta_file = self.project.metainf()
        with open(meta_file,'w+') as meta:
            json.dump(self.meta, meta, indent=tabs)

    def initialize(self, path=None, fields=None, clear=False):
        """Initialize the index object by parsing the index file
        """
        if clear:
            self.entries = {}
            self.meta = {}
        if not self.entries:
            if not path and self.project:
                path = self.project.indexfile()
            if fields:
                self.meta['metainfo'].extend(fields)
            if not path or not os.path.exists(path):
                return False
            with open(path, 'r') as index_file:
                for line in index_file:
                    self._parse_line(line)
            if path:
                self.export()

    def _parse_line(self, line):
        """Parse a line of the index file and append the parsed entry to the entries list.

        Arguments:
        ----------
        line - the line to be parsed
        """
        expr = '^(?P<file>.+)\t(?P<tags>.+)$'
        match = re.match(expr, line)
        file = match.group('file')
        tags = match.group('tags')
        if self.type == IndexType.META and file != '.' or self.type == IndexType.DATA and file == '.':
            raise ValueError('Index type %s not valid for this index file' % IndexType.get(self.type))

        meta = Metadata.parse(tags, self.meta['metainfo']+[self.meta['id']])
        entry = self.entries.get(meta.get(self.meta['id']), None)

        if not entry:
            entry = IndexEntry(meta, self.meta)
            self.entries[entry.id] = entry

        if self.type == IndexType.DATA:
            file_info = Metadata.parse(tags, self.meta['fileinfo'])
            file_info.add({'path': file})
            entry.add_file(file_info)

    def import_sv(self, path, sep='\t', id=''):
        """Import entries from a SV file. The sv file must have an header line with the name of the properties.

        Arguments:
        ----------
        path - path to the sv files to be imported
        """

        with open(path,'r') as sv_file:
            header = sv_file.readline().rstrip().split(sep)
            print header
            if not self.meta:
                self.meta['metainfo'] = header
            if id:
                self.meta['id'] = id
            else:
                self.meta['id'] = header[0]
            for line in sv_file:
                meta = Metadata(header, dict(zip(header, map(lambda x : x.replace(' ', '_'), line.rstrip().split(sep)))))
                entry = self.entries.get(meta.get(self.meta['id']), None)

                if not entry:
                    entry = IndexEntry(meta, self.meta)
                    self.entries[entry.id] = entry
            self.export()

    def export(self, out=None):
        """Save changes made to the index structure loaded in memory to the index file
        """
        if not out:
            if self.project:
                out = open(self.project.indexfile(),'w+')
            else:
                out = sys.stdout
        for entry in self.entries.values():
            out.writelines('\n'.join(entry.export()))
        out.writelines('\n')

