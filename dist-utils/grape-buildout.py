#!/usr/bin/python
import sys
import os
import site

# hack the python path
__gt_cwd__dir = os.path.split(os.path.split(os.path.abspath(__file__))[0])[0]
__gt_py_version = sys.version_info
site.addsitedir("%s/lib/python%d.%d/site-packages" % (__gt_cwd__dir, __gt_py_version[0], __gt_py_version[1]))

if __name__ == '__main__':
    import grape.commands
    grape.commands.buildout()
