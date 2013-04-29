"""The index module provides functionality around grape data indexing
"""
import re

class Metadata(object):
    """A class to store metadata retrieved from indices

    The keys of the tags are mapped to the Metadata class properties dinamically.
    The class properties name and values are derived form a dictionary
    passed as an argument to the contructor.
    """

    """Create an instance of a Metadata class

    Arguments:
    ----------
    kwargs - a dictionary containing name and values of the tags
    """
    def __init__(self, kwargs):
        for key in kwargs:
            if key in self.__dict__.keys():
                raise ValueError("%r already contains %r property" % (self.__class__,key))
            self.__dict__[key]=kwargs[key]

    """Get the value of a tag given its key

    Arguments:
    -----------
    key - the key of the tag
    """
    def get(self, key):
        if not key in self.__dict__.keys():
            raise ValueError('Key %r not found' % key)
        return self.__dict__[key]

    """Concatenate specified tags using the provided tag separator. The tag are formatted
    according to the 'index file' format

    Keyword arguments:
    -----------
    tags - list of keys identifying the tags to be concatenated. Default value is
           the empty list, which means that all tags will be returned.
    sep  - the tag separator character. The default value is a <space> according to
           the 'index file' format.
    """
    def get_tags(self, tags=[], sep=' '):
        tag_list = []
        if not tags:
            tags = self.__dict__.keys()
        for key in tags:
            tag_list.append(self.get_tag(key))
        return sep.join(tag_list)

    """Return a key/value pair for a give tag, formatted according to the 'index file' format

    Arguments:
    -----------
    key   -  the key of the tag

    Keyword arguments:
    -------------------
    sep   -  the separator between key and value of the tag. Default is '='.
    trail -  trailing character of the tag. Default ';'.

    """
    def get_tag(self, key, sep='=', trail=';'):
        value = self.get(key)
        return sep.join([key,str(value)])+trail

    """Parse a string of concatenated tags and converts it to a Metadata object

    Arguments:
    ----------
    string - the concatenated tags
    """
    @classmethod
    def parse(cls, string):
        tags = cls.__parse_tags(string)
        return Metadata(tags)

    """Parse key/value pair tags from a string and returns a dictionary

    Arguments:
    ----------
    str - the tags string

    Keyword arguments:
    ------------------
    sep   -  the separator between key and value of the tag. Default is '='.
    trail -  trailing character of the tag. Default ';'.
    """
    @classmethod
    def _parse_tags(cls, str, sep='=', trail=';'):
        tags = {}
        expr = '(?P<key>[^ ]+)%s(?P<value>[^%s]+)%s' % (sep,trail,trail)
        for match in re.finditer(expr, str):
            tags[match.group('key')] = match.group('value')
        return tags

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
            'META' : cls.META,
            'DATA' : cls.DATA,
            cls.META : 'META',
            cls.DATA : 'DATA'
        }.get(str,None)


class Index(object):
    """A class to access information stored into 'index files'.
    """

    """Creates an instance of an Index class

    Arguments:
    ----------
    path - path of the index file

    Keyword arguments:
    ------------------
    type    -  a :class:IndexType type. Default is DATA
    entries -  a list containing all the entries as dictionaries. Default empty list.
    """
    def __init__(self, path, type=IndexType.DATA, entries=[]):
        self.path = path
        self.type = type

        self.entries = entries

    """Initialize the index obect by parsing the index file
    """
    def initialize(self):
        with open(self.path, 'r') as index_file:
            for line in index_file:
                self._parse_line(line)

    """Parse a line of the index file and append the parsed entry to the entries list.

    Arguments:
    ----------
    line - the line to be parsed
    """
    def _parse_line(self, line):
        expr = '^(?P<file>.+)\t(?P<tags>.+)$'
        match = re.match(expr, line)

        self.entries.append({'file': match.group('file'), 'metadata': Metadata.parse(match.group('tags'))})

