"""Recipe opencmiss"""

import logging
import os
import os.path
import re
import shutil
import tempfile

import zc.buildout.easy_install

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
        # Utilities
        utils_root = os.path.join(tmp, 'utilities')
        utils_build_path = os.path.join(tmp, 'utilities', 'manage', 'build')
        utils_mod_path = os.path.join(utils_root, 'cmake-2.8', 'Modules')
        os.makedirs(utils_build_path)
        os.chdir(utils_build_path)
        system('svn co '
            'https://svn.physiomeproject.org/svn/opencmiss/utilities/trunk/ '
            '.. --depth=files')
        system('cmake ..')
        system('cmake --build .')

        # Utilities
        deps_root = os.path.join(tmp, 'dependencies')
        deps_build_path = os.path.join(tmp, 'dependencies', 'manage', 'build')
        deps_install_path = os.path.join(tmp, 'dependencies', 'install')
        os.makedirs(deps_build_path)
        os.chdir(deps_build_path)
        system('svn co '
            'https://svn.physiomeproject.org/svn/opencmiss/dependencies/trunk/'
            ' .. --depth=files')
        system('cmake '
            '-DDEPENDENCIES_ROOT=%s '
            '-DDEPENDENCIES_MODULE_PATH=%s '
            '-DDEPENDENCIES_SVN_REPO='
                'https://svn.physiomeproject.org/svn/'
                    'opencmiss/dependencies/trunk/ ..' % (
                deps_root,
                utils_mod_path
            )
        )
        system('cmake --build .')

        # Zinc Library
        zinc_root = os.path.join(tmp, 'zinc')
        os.makedirs(zinc_root)

        zinc_src_path = os.path.join(tmp, 'zinc', 'library')
        zinc_lib_build_path = os.path.join(tmp, 'build', 'zinc', 'library')
        os.makedirs(zinc_lib_build_path)
        system('svn co '
            'https://svn.physiomeproject.org/svn/cmiss/zinc/library/trunk/ ' +
            zinc_src_path)
        os.chdir(zinc_lib_build_path)
        system('cmake '
            '-DZINC_DEPENDENCIES_INSTALL_PREFIX=%s '
            '-DZINC_MODULE_PATH=%s '
            '-DCMAKE_INSTALL_PREFIX:PATH=%s '
            '-DCMAKE_INSTALL_RPATH:PATH=%s/lib '
            '%s' % (
                deps_install_path,
                utils_mod_path,
                dest,
                dest,
                zinc_src_path,
            )
        )
        system('cmake --build .')
        system('cmake -P cmake_install.cmake')

        # Zinc Python Bindings

        pyzinc_co_path = os.path.join(zinc_root, 'bindings')
        pyzinc_src_path = os.path.join(pyzinc_co_path, 'python')
        pyzinc_build_path = os.path.join(tmp, 'build', 'zinc', 'bindings')
        os.makedirs(pyzinc_build_path)
        system('svn co '
            'https://svn.physiomeproject.org/svn/cmiss/zinc/bindings/trunk/ ' +
            pyzinc_co_path)
        os.chdir(pyzinc_build_path)
        system('cmake '
            '-DZinc_DIR=%s/lib '
            '-DPYZINC_MODULE_PATH=%s '
            '-DCMAKE_INSTALL_PREFIX:PATH=%s '
            '%s' % (
                dest,
                utils_mod_path,
                dest,
                pyzinc_src_path,
            )
        )
        system('cmake --build .')
        # prepare an egg for distribution
        system('python setup.py bdist_egg')
        # invoke the installation with zc.buildout

        zc.buildout.easy_install.install(
            specs=['pyzinc'], 
            dest=self.buildout['buildout']['develop-eggs-directory'],
            links=['file://' + pyzinc_build_path + '/dist/'],
            index=None,
            executable=self.executable,
            path=[self.buildout['buildout']['eggs-directory']]
        )

        return None
