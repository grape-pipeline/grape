"""The index module provides functionality around grape data indexing
"""
import re


class Metadata(object):
    """A class to store metadata retrieved from indices

    The keys of the tags are mapped to the Metadata class properties dinamically.
    The class properties name and values are derived form a dictionary
    passed as an argument to the contructor.
    """

    metainfo = ['labExpId',   # TODO: not hardcode this information
                'labProtocolId',
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


    def __init__(self, kwargs):
        """Create an instance of a Metadata class

        Arguments:
        ----------
        kwargs - a dictionary containing name and values of the tags
        """
        self.file_info = {}

        for key in kwargs:
            if key in self.__dict__.keys():
                raise ValueError("%r already contains %r property" % (self. __class__, key))
            if key in Metadata.metainfo:
                self.__dict__[key] = kwargs[key]
            else:
                self.file_info[key] = kwargs[key]

    def getId(self):
        """Get the key of the identifier for the metadata info
        """
        return self.__dict__.get('labExpId') #TODO: implement definitions file

    def get(self, key):
        """Get the value of a tag given its key

        Arguments:
        -----------
        key - the key of the tag
        """
        if not key in self.__dict__.keys():
            raise ValueError('Key %r not found' % key)
        return self.__dict__[key]

    def get_tags(self, tags=[], sep=' '):
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
        exclude = ['file_info']
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
        return sep.join([key, str(value)])+trail

    def contains(self, key):
        """Return true if the metadata contains the specified key
        """
        return self.__dict__.has_key(key)


    @classmethod
    def parse(cls, string):
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


class IndexEntry():
    """A class that represent dataset entry in the index file.

    Each entry is identified by the dataset name (eg. labExpId) and has metadata
    information as long as file information in order to be able to retrieve files
    and information related to the sample.
    """

    types = ['fastq', 'bam', 'bai', 'gff', 'map', 'bigWig', 'bed']
    fileinfo = []

    def __init__(self, metadata):
        """Create an instance of the IndexEntry class

        Arguments:
        ----------
        metadata -  an instance of :class:Metadata that contains the parsed metadata
                    information
        """
        self.views = {}
        self.metadata = metadata
        self.id = self.metadata.getId()

    def add_view(self, path, type, view):
        """Add the path of a file related to the dataset to the class files dictionary

        Arguments:
        ----------
        path - the path to te file to be added
        type - the type of the file
        view - the data view representing the file
        """
        if type not in IndexEntry.types:
            raise ValueError('Tyoe not supported: %r' % type)
        self.views[view] = path

class IndexType():
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


class Index(object):
    """A class to access information stored into 'index files'.
    """

    def __init__(self, path, type=IndexType.DATA, entries={}):
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

    def initialize(self):
        """Initialize the index obect by parsing the index file
        """
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
            raise ValueError('Index type %s does not support this index file' % IndexType.get(self.type))

        meta = Metadata.parse(tags)

        entry = self.entries.get(meta.getId(),None)

        if not entry:
            entry = IndexEntry(meta)
            self.entries[entry.id] = entry

        entry.add_view(file, meta.file_info.get('type'), meta.file_info.get('view'))
