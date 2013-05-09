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
        value = self.get(key)
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


class IndexEntry():
    """A class that represent dataset entry in the index file.

    Each entry is identified by the dataset name (eg. labExpId) and has metadata
    information as long as file information in order to be able to retrieve files
    and information related to the sample.
    """

    def __init__(self, metadata, index_meta):
        """Create an instance of the IndexEntry class

        Arguments:
        ----------
        metadata -  an instance of :class:Metadata that contains the parsed metadata
                    information
        """
        self.files = {}
        self.metadata = metadata
        self.index_meta = index_meta
        self.id = metadata.get(index_meta['id'])

    def add_file(self, file_info):
        """Add the path of a file related to the dataset to the class files dictionary

        Arguments:
        ----------
        file_info - a :class:Metadata object containing the file information
        """
        type = file_info.type
        if not self.index_meta['file_types']:
            self.index_meta['file_types'].append(type)
        if type not in self.index_meta['file_types']:
            raise ValueError('Type not supported: %r' % type)
        if not self.files.get(type, None):
            self.files[type] = []
        self.files[type].append(file_info)
        self.files[type]=sorted(self.files[type], key=lambda file: file.path)

    def export(self, absolute=False, types=[]):
        """Convert an index entry object to its string representation in index file format
        """
        out = []
        if not types:
            types = self.files.keys()
        for type in types:
            for file in self.files[type]:
                path = file.path
                if absolute:
                    path = os.path.abspath(path)
                tags = ' '.join([self.metadata.get_tags(),file.get_tags(exclude=['path',self.index_meta['id']])])
                out.append('\t'.join([path, tags]))
        return out


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

