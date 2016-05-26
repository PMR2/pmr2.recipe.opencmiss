"""Recipe opencmiss"""

import logging
import os
import os.path
import re
import shutil
import tempfile
from subprocess import check_output

import zc.buildout.easy_install

almost_environment_setting = re.compile('\w+=').match
not_starting_with_digit = re.compile('\D').match

def system(c):
    if os.system(c):
        raise SystemError("Failed", c)


class Recipe(object):
    """
    Recipe for building OpenCMISS.

    Encapsulates the instructions as found at

    http://physiomeproject.org/software/opencmiss/zinc/documentation/support/build
    
    """

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options
        directory = buildout['buildout']['directory']
        self.git_checkout = options.get('git-checkout', 'devel')

        environ = []
        for token in self.options.get('environment', '').split():
            if (almost_environment_setting(token) and
                not_starting_with_digit(token)):
                environ.append(token)
            else:
                if environ:
                    environ[-1] += ' ' + token
                else:
                    raise ValueError('Bad environment setting', token)

        if environ:
            self.environ = dict([x.split('=', 1) for x in environ])
        else:
            self.environ = {}

        location = os.path.join(options.get(
                'location', buildout['buildout']['parts-directory']), name)

        options['location'] = location
        
        python = options.get('python', buildout['buildout']['python'])
        self.executable = buildout[python]['executable']


    def install(self):
        """Installer"""
        self.build()
        return self.options['location']

    def update(self):
        if not os.path.isdir(self.options['location']):
            self.build()

    def build(self):
        """
        Based upon zc.recipe.cmmi
        """
        logger = logging.getLogger(self.name)

        # now unpack and work as normal
        tmp = tempfile.mkdtemp('buildout-'+self.name)

        for key, value in sorted(self.environ.items()):
            logger.info('Updating environment: %s=%s' % (key, value))
        os.environ.update(self.environ)

        dest = self.options['location']
        if not os.path.exists(dest):
            os.mkdir(dest)

        try:
            here = os.getcwd()
            os.chdir(tmp)
            try:
                self.make(tmp, dest)
                shutil.rmtree(tmp)
            finally:
                os.chdir(here)
        except:
            shutil.rmtree(dest)
            if os.path.exists(tmp):
                logger.error("package build failed: %s", tmp)
            raise

    def make(self, tmp, dest):
        # Checkout
        os.chdir(tmp)
        build_path = os.path.join(tmp, 'manage', 'build')
        system('git clone https://github.com/OpenCMISS/manage')
        os.chdir(build_path)
        system('git checkout %s' % self.git_checkout)
        cmake_bin = 'cmake'

        # Check cmake version
        v = tuple(check_output(['cmake', '--version']).splitlines()[0].rsplit(
            ' ', 1)[-1].split('.'))
        if v < ('3', '4'):
            # build cmake>=3.4 and restart cmake with the built version.
            system('cmake ..')
            system('make cmake')
            cmake_bin = os.path.join(
                '..', '..', 'install', 'utilities', 'cmake', 'bin', 'cmake')

        fd = open('OpenCMISSLocalConfig.cmake', 'a')
        fd.write('\n')
        #fd.write('set(BUILD_TESTS "NO")\n')
        fd.write('set(OC_PYTHON_BINDINGS_USE_VIRTUALENV "NO")\n')
        fd.write('set(OC_USE_ARCHITECTURE_PATH "NO")\n')
        fd.write('set(OPENCMISS_INSTALL_ROOT "%s")\n' % dest)
        fd.close()
        system(cmake_bin + ' ..')
        system('make install')
        # ``make install`` will also install the develop-egg correctly
        # into develop-eggs.

        # If the actual egg is wanted
        # py_path = os.path.join(dest, 'release', 'python', 'RELEASE')
        # os.chdir(py_path)
        # system('python setup.py bdist_egg')
        # Egg in this dir:
        # py_path = os.path.join(py_path, 'dist')

        return None
