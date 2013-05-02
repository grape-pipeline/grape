"""The index module provides functionality around grape data indexing
"""
import re
import os


class Metadata(object):
    """A class to store metadata retrieved from indices

    The keys of the tags are mapped to the Metadata class properties dinamically.
    The class properties name and values are derived form a dictionary
    passed as an argument to the contructor.
    """

    def __init__(self, tags, kwargs):
        """Create an instance of a Metadata class

        Arguments:
        ----------
        kwargs - a dictionary containing name and values of the tags
        """
        for key in kwargs:
            if key in self.__dict__.keys():
                raise ValueError("%r already contains %r property" % (self. __class__, key))
            if key == IndexDefinition.id:
                self.id = str(kwargs[key])
                continue
            if key in tags:
                self.__dict__[key] = str(kwargs[key])

    def get(self, key):
        """Get the value of a tag given its key

        Arguments:
        -----------
        key - the key of the tag
        """
        if not key in self.__dict__.keys():
            raise ValueError('Key %r not found' % key)
        return self.__dict__[key]

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
        value = self.get(key)
        if key == 'id':
            key = IndexDefinition.id
        return sep.join([key, str(value)])+trail

    def add(self, dict):
        """Add properties to the :class:Metadata object from a dictionary

        Arguments:
        ----------
        dict - the dictionary conatining the key/value pairs to be added
        """
        for key in dict.keys():
            if key in self.__dict__.keys():
                raise ValueError("%r already contains %r property" % (self. __class__, key))
            self.__dict__[key] = str(dict[key])

    def contains(self, key):
        """Return true if the metadata contains the specified key

        Arguments:
        ----------
        key - the key to look for
        """
        return self.__dict__.has_key(key)


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


class IndexEntry():
    """A class that represent dataset entry in the index file.

    Each entry is identified by the dataset name (eg. labExpId) and has metadata
    information as long as file information in order to be able to retrieve files
    and information related to the sample.
    """

    def __init__(self, metadata):
        """Create an instance of the IndexEntry class

        Arguments:
        ----------
        metadata -  an instance of :class:Metadata that contains the parsed metadata
                    information
        """
        self.files = {}
        self.metadata = metadata
        self.id = self.metadata.id

    def add_file(self, file_info):
        """Add the path of a file related to the dataset to the class files dictionary

        Arguments:
        ----------
        file_info - a :class:Metadata object containing the file information
        """
        type = file_info.type
        if not IndexDefinition.file_types:
            IndexDefinition.file_types.append(type)
        if type not in IndexDefinition.file_types:
            raise ValueError('Type not supported: %r' % type)
        if not self.files.get(type, None):
            self.files[type] = []
        self.files[type].append(file_info)
        self.files[type]=sorted(self.files[type], key=lambda file: file.path)

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
##### TODO: not hardcode this information ##############################
    id = 'labExpId'
    metainfo = ['labProtocolId',
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
    fileinfo = ['type',
                'size',
                'md5',
                'view'
                ]

    file_types = ['fastq', 'bam', 'bai', 'gff', 'map', 'bigWig', 'bed']

    default_path = '.index'
######################################################################


class Index(object):
    """A class to access information stored into 'index files'.
    """

    def __init__(self, path=None, type=IndexType.DATA, entries={}):
        """Creates an instance of an Index class

        Arguments:
        ----------
        path - path of the index file

        Keyword arguments:
        ------------------
        type    -  a :class:IndexType type. Default is DATA
        entries -  a list containing all the entries as dictionaries. Default empty list.
        """

        self.path = path
        self.type = type

        self.entries = entries

        if not self.path:
            self.path = IndexDefinition.default_path

    def initialize(self):
        """Initialize the index object by parsing the index file
        """
        if not os.path.exists(self.path):
            self.entries = {}
        else:
            with open(self.path, 'r') as index_file:
                for line in index_file:
                    self._parse_line(line)

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

        meta = Metadata.parse(tags, IndexDefinition.metainfo)
        entry = self.entries.get(meta.id, None)

        if not entry:
            entry = IndexEntry(meta)
            self.entries[entry.id] = entry

        if self.type == IndexType.DATA:
            file_info = Metadata.parse(tags, IndexDefinition.fileinfo)
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
            if id:
                IndexDefinition.id = id
            else:
                IndexDefinition.id = header[0]
            for line in sv_file:
                meta = Metadata(header, dict(zip(header, map(lambda x : x.replace(' ', '_'), line.rstrip().split(sep)))))
                entry = self.entries.get(meta.id, None)

                if not entry:
                    entry = IndexEntry(meta)
                    self.entries[entry.id] = entry
