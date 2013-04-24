from fnmatch import fnmatch
from zc.buildout.download import Download
from zc.buildout import UserError

import sys
import logging
import os.path
import setuptools.archive_util
import shutil
import tempfile
import zc.buildout
import subprocess

if sys.version_info[0] > 2:
    import urllib.parse as urlparse
else:
    import urlparse


TRUE_VALUES = ('yes', 'true', '1', 'on')
GRAPE_HOME = 'GRAPE_HOME'

class Recipe(object):
    """Recipe for downloading packages from the net and extracting them on
    the filesystem.
    """

    def __init__(self, buildout, name, options):
        self.options = options
        self.buildout = buildout
        self.name = name

        options.setdefault('strip-top-level-dir', 'false')
        options.setdefault('ignore-existing', 'false')
        options.setdefault('download-only', 'false')
        options.setdefault('hash-name', 'false')
        options.setdefault('on-update', 'true')
        options['filename'] = options.get('filename', '').strip()

        log = logging.getLogger(self.name)
        if not options.get('name'):
            log.warning('Module name was not specified - using part name')
            options['name'] = self.name

        if not options.get('version'):
            log.error('Unable to get the %s version from the configuration file', self.name)
            raise UserError('Module version is mandatory')

        if options.get('mode'):
          options['mode'] = options['mode'].strip()

        # buildout -vv (or more) will trigger verbose mode
        self.verbose = int(buildout['buildout'].get('verbosity', 0)) >= 20
        self.excludes = [x.strip() for x in options.get('excludes', '').strip().splitlines() if x.strip()]

    def progress_filter(self, src, dst):
        """Filter out contents from the extracted package."""
        log = logging.getLogger(self.name)
        for exclude in self.excludes:
            if fnmatch(src, exclude):
                if self.verbose:
                    log.debug("Excluding %s" % src.rstrip('/'))
                self.excluded_count = self.excluded_count + 1
                return
        return dst

    def get_destination(self):
       grape_home = os.getenv(GRAPE_HOME, os.path.join(os.getenv('HOME'), 'grape'))
       return os.path.join(grape_home, 'modules')


    def update(self):
        pass
        #if self.options['on-update'].strip().lower() in TRUE_VALUES:
        #    self.install()

    def calculate_base(self, extract_dir):
        """
        recipe authors inheriting from this recipe can override this method to set a different base directory.
        """
        log = logging.getLogger(self.name)
        # Move the contents of the package in to the correct destination
        top_level_contents = os.listdir(extract_dir)
        if len(top_level_contents) != 1:
            log.error('Unable to strip top level directory because there are more '
                      'than one element in the root of the package.')
            raise zc.buildout.UserError('Invalid package contents')
        base = os.path.join(extract_dir, top_level_contents[0])
        return base

    def install(self):
        log = logging.getLogger(self.name)

        destination = self.get_destination()

        module = {'name' : self.options['name'], 'version' : self.options['version']}
        url = self.options['url']
        md5 = self.options.get('md5sum')

        parts = []

        if os.path.isdir(os.path.join(destination, module['name'], module['version'])):
            log.error('Skipping module %s-%s - already installed', module['name'], module['version'])
        else:

            download = Download(self.buildout['buildout'], hash_name=self.options['hash-name'].strip() in TRUE_VALUES)
            path, is_temp = download(url, md5sum=md5)

            try:

                # Create destination directory
                module_dir = os.path.join(destination, module['name'])
                if not os.path.isdir(module_dir):
                    os.makedirs(module_dir)

                version_dir = os.path.join(module_dir, module['version'])

                os.makedirs(version_dir)

                parts.append(version_dir)

                download_only = self.options['download-only'].strip().lower() in TRUE_VALUES
                if download_only:
                    if self.options['filename']:
                        # Use an explicit filename from the section configuration
                        filename = self.options['filename']
                    else:
                        # Use the original filename of the downloaded file regardless
                        # whether download filename hashing is enabled.
                        # See http://github.com/hexagonit/hexagonit.recipe.download/issues#issue/2
                        filename = os.path.basename(urlparse.urlparse(self.options['url'])[2])

                    # Copy the file to destination without extraction
                    target_path = os.path.join(version_dir, filename)
                    shutil.copy(path, target_path)
                    if self.options.get('mode'):
                        os.chmod(target_path, int(self.options['mode'], 8))
                    if not version_dir in parts:
                        parts.append(target_path)
                else:
                    # Extract the package
                    extract_dir = tempfile.mkdtemp("buildout-" + self.name)
                    self.excluded_count = 0
                    try:
                        try:
                            setuptools.archive_util.unpack_archive(path, extract_dir, progress_filter=self.progress_filter)
                        except setuptools.archive_util.UnrecognizedFormat:
                            log.error('Unable to extract the package %s. Unknown format.', path)
                            raise zc.buildout.UserError('Package extraction error')
                        if self.excluded_count > 0:
                            log.info("Excluding %s file(s) matching the exclusion pattern." % self.excluded_count)
                        base = self.calculate_base(extract_dir)

                        log.info('Extracting module package to %s' % version_dir)

                        ignore_existing = self.options['ignore-existing'].strip().lower() in TRUE_VALUES
                        for filename in os.listdir(base):
                            dest = os.path.join(version_dir, filename)

                            if os.path.exists(dest):
                                if ignore_existing:
                                    log.info('Ignoring existing target: %s' % dest)
                                else:
                                    log.error('Target %s already exists. Either remove it or set '
                                              '``ignore-existing = true`` in your buildout.cfg to ignore existing '
                                              'files and directories.', dest)
                                    raise zc.buildout.UserError('File or directory already exists.')
                            else:
                                # Only add the file/directory to the list of installed
                                # parts if it does not already exist. This way it does
                                # not get accidentally removed when uninstalling.
                                parts.append(dest)

                            if os.path.islink(os.path.join(base,filename)):
                                real_path = os.path.realpath(os.path.join(base,filename))
                                # shutils move has a problem with symlinks
                                # probabluy for a good reason, but we need
                                # to meve everything as is. Workaround for now
                                # is just to performe a system move
                                p = subprocess.Popen(["mv",
                                                      os.path.join(base, filename),
                                                      dest]).wait()
                                if p != 0:
                                    raise Exception("Failed to move symlink")
                            else:
                                shutil.move(os.path.join(base, filename), dest)
                    finally:
                        shutil.rmtree(extract_dir)

            finally:
                if is_temp:
                    os.unlink(path)

        return parts
