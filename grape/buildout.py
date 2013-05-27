#!/usr/bin/env python
"""The Grape buildout module provides ways to
access the installed modules in GRAPE_HOME
"""
from zc.buildout import UserError
from zc.buildout.buildout import Buildout as Bout
from .grape import GrapeError, Grape

import os
import logging

class Buildout(Bout):
    """A grape buildout class extending the zc.buildout
    """

    def __init__(self, config_file):
        #if not os.path.exists(buildout_conf):
        #    raise GrapeError("No buildout configuration file found!")
        #else:
        try:
            Bout.__init__(self,config_file,[])
        except UserError as e:
            raise GrapeError(str(e))
        self['buildout']['installed'] = ''
        self._type = 'tar'

    def _setup_directories(self):
        if self._type == 'egg':
            Bout._setup_directories(self)

    def install(self, install_args):
        Bout.install(self,install_args)
        if self._type == 'tar':
            self.cleanup()

    def cleanup(self):
        """ Cleanup method to remove the directories created by buildout """
        for name in ('bin', 'develop-eggs', 'eggs', 'parts'):
            logger = logging.getLogger('buildout')
            dir = self['buildout'][name+'-directory']
            if os.path.isdir(dir):
                logger.warn('Removing directory %r.', dir)
                os.removedirs(dir)

class Module(object):
    """A grape buildout module that can be activated in the current
    environment.
    """

    def __init__(self, directory):
        self.directory = directory

    def activate(self):
        """Activate this module and load its configuration into the current
        environment.
        """
        # the default implementation simply puts the bin folder in path
        bin_path = os.path.join(self.directory, "bin")
        if os.path.exists(bin_path):
            Module.__prepend_environment("PATH", bin_path)

    @staticmethod
    def __prepend_environment(source, value, delim=":"):
        """Prepend the given value to the source environment variable
        using the given delimiter
        """
        current = ""
        if source in os.environ:
            current = delim + os.environ[source]
        os.environ[source] = "%s%s" % (value, current)


def find(name, version=None, grape_home=None):
    """Using the grape home in teh given :class:grape.Grape instance,
    this searches for the module with the given name and version. If no
    version is specified, all detected versions are sorted alpha-numerically
    and the latest one is returned.

    Paramter
    --------
    grape_home   - the grape home folder used to search for modules
    name         - the name of the module
    version      - the version of the module. Default is to return the
                   latest one
    """
    if grape_home is None:
        grape_home = Grape().home
    if name is None:
        raise AttributeError("None name not permitted")
    if grape_home is None:
        raise ValueError("GRAPE_HOME not defined. Please set the GRAPE_HOME"
                         " environment variable!")
    if not os.path.exists(grape_home):
        raise ValueError("Grape home %s not found!" % (grape_home))

    module_dir = os.path.join(grape_home, "modules/%s" % (name))
    if not os.path.exists(module_dir):
        raise ValueError("Module %s not found in %s" % (name, grape_home))
    version_dir = None
    if version is not None:
        version_dir = os.path.join(module_dir, version)
    else:
        # scan version
        sorted_version = sorted(os.listdir(module_dir))
        if len(sorted_version) == 0:
            raise ValueError("No versions found for %s" % (name))
        version_dir = os.path.join(module_dir, sorted_version[0])

    if not os.path.exists(version_dir):
        raise ValueError("Module %s/%s not found in %s" % (name,
                                                           version,
                                                           grape_home))
    return Module(version_dir)
