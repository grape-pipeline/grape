"""The index module provides functionality around grape data indexing
"""
import re

class Metadata(object):
    """A class to store metadata retrieved from indices
    """

    def __init__(self, kwargs):
        for key in kwargs:
            if key in self.__dict__.keys():
                raise ValueError("%r already contains %r property" % (self.__class__,key))
            self.__dict__[key]=kwargs[key]

    def get(self, key):
        if not key in self.__dict__.keys():
            raise ValueError('Key %r not found' % key)
        return self.__dict__[key]

    def get_tags(self, tags=[], sep=' '):
        tag_list = []
        if not tags:
            tags = self.__dict__.keys()
        for key in tags:
            tag_list.append(self.get_tag(key))
        return sep.join(tag_list)

    def get_tag(self, key, sep='=', trail=';'):
        value = self.get(key)
        return sep.join([key,str(value)])+trail

class IndexType():
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
    """A class to access information stored into index files
    """

    def __init__(self, path, type=IndexType.DATA, entries=[]):
        self.path = path
        self.type = type

        self.entries = entries

    def initialize(self):
        with open(self.path, 'r') as index_file:
            for line in index_file:
                self._parse_line(line)

    def _parse_tags(self, str, sep='=', trail=';'):
        tags = {}
        expr = '(?P<key>[^ ]+)%s(?P<value>[^%s]+)%s' % (sep,trail,trail)
        for match in re.finditer(expr, str):
            tags[match.group('key')] = match.group('value')
        return tags

    def _parse_tag(sef, str, sep='=', trail=';'):
        expr = '(?P<key>[^ ]+)%s(?P<value>[^%s]+)%s' % (sep,trail,trail)
        match = re.match(expr,str)
        return [match.group('key'), match.group('value')]

    def _parse_line(self, line):
        expr = '^(?P<file>.+)\t(?P<tags>.+)$'
        match = re.match(expr, line)
        tags = self._parse_tags(match.group('tags'))

        self.entries.append({'file': match.group('file'), 'metadata': Metadata(tags)})
