#!/usr/bin/env python
import os
import subprocess

from setuptools import setup, find_packages
from setuptools import Command
from setuptools.command.test import test as TestCommand
from setuptools.command.build_py import build_py
import distutils.log
from distutils.spawn import find_executable


class BuildPyCommand(build_py):

    def run(self):
        # ensure smoketest_config.json is generated
        from raiden.tests.utils.smoketest import load_or_create_smoketest_config
        load_or_create_smoketest_config()
        build_py.run(self)


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


class CompileWebUI(Command):
    description = 'use npm to compile webui code to raiden/ui/web/dist'
    user_options = [
        ('dev', 'D', 'use development preset, instead of production (default)'),
    ]

    def initialize_options(self):
        self.dev = None

    def finalize_options(self):
        pass

    def run(self):
        npm = find_executable('npm')
        if not npm:
            self.announce('NPM not found. Skipping webUI compilation', level=distutils.log.WARN)
            return
        npm_run = 'build:prod'
        if self.dev is not None:
            npm_run = 'build:dev'

        cwd = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                'raiden',
                'ui',
                'web',
            ),
        )

        npm_version = subprocess.check_output([npm, '--version'])
        # require npm 4.x.x or later
        if not int(npm_version.split(b'.')[0]) >= 4:
            self.announce(
                'NPM 4.x or later required. Skipping webUI compilation',
                level=distutils.log.WARN,
            )
            return

        command = [npm, 'install']
        self.announce('Running %r in %r' % (command, cwd), level=distutils.log.INFO)
        subprocess.check_call(command, cwd=cwd)

        command = [npm, 'run', npm_run]
        self.announce('Running %r in %r' % (command, cwd), level=distutils.log.INFO)
        subprocess.check_call(command, cwd=cwd)

        self.announce('WebUI compiled with success!', level=distutils.log.INFO)


with open('README.rst') as readme_file:
    readme = readme_file.read()


history = ''

install_requires_replacements = {
    'git+https://github.com/LefterisJP/pystun@develop#egg=pystun': 'pystun',
    (
        'git+https://github.com/raiden-network/raiden-libs.git'
        '@f40a867f5d8ea89b1386fd6cc4c66f8eff886fea'
        '#egg=raiden-libs'
    ): 'raiden-libs',
    (
        'git+https://github.com/raiden-network/raiden-contracts.git'
        '@2ab91aa4b062d88a124ce050551e2f4b8cb0da57#egg=raiden-contracts'
    ): 'raiden-contracts',
}

install_requires = list(set(
    install_requires_replacements.get(requirement.strip(), requirement.strip())
    for requirement in open('requirements.txt') if not requirement.lstrip().startswith('#')
))

test_requirements = []

version = '0.4.0'  # Do not edit: this is maintained by bumpversion (see .bumpversion_client.cfg)

setup(
    name='raiden',
    description='',
    long_description=readme + '\n\n' + history,
    author='Brainbot Labs Est.',
    author_email='contact@brainbot.li',
    url='https://github.com/raiden-network/raiden',
    packages=find_packages(),
    include_package_data=True,
    license='MIT',
    zip_safe=False,
    keywords='raiden',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass={
        'test': PyTest,
        'compile_webui': CompileWebUI,
        'build_py': BuildPyCommand,
    },
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=install_requires,
    tests_require=test_requirements,
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'raiden = raiden.__main__:main',
        ],
    },
)
