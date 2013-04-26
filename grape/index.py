"""The index module provides functionality around grape data indexing
"""

class Metadata(object):
    """A class to store metadata retrieved from indices
    """

    def __init__(self, **kwargs):
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

class Index(object):
    """A class to access information stored into index files
    """

    def __init__(self, path):
        self.path = path


