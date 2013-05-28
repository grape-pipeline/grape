#!/usr/bin/env python
import sys
import os
import site

def readlinkabs(l):
    """Recursively resolve sym links and return the absolute
    path to the final destination
    """
    if not os.path.islink(l):
        return os.path.abspath(l)
    p = os.path.normpath(os.readlink(l))
    if os.path.isabs(p):
        return readlinkabs(p)
    return readlinkabs(os.path.join(os.path.dirname(l), p))

def get_grape_home():
    """Resolve the grape installation base direcory"""
    return os.path.split(os.path.split(readlinkabs(__file__))[0])[0]

def set_grape_home_env(home):
    """Set the GRAPE_HOME environment variable if not already set"""
    if os.getenv("GRAPE_HOME", None) is None:
        os.environ["GRAPE_HOME"] = home

# hack the python path
__install_dir = get_grape_home()
__py_version = sys.version_info
site.addsitedir("%s/lib/python%d.%d/site-packages" % (__install_dir, __py_version[0], __py_version[1]))
set_grape_home_env(__install_dir)

if __name__ == '__main__':
    import grape.commands
    grape.commands.buildout()
