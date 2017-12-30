import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


with open(os.path.join(os.path.dirname(__file__), 'nativeconfig', 'version.py')) as f:
    VERSION = None
    code = compile(f.read(), 'version.py', 'exec')
    exec(code)
    assert VERSION


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    version=VERSION,
    cmdclass={'test': PyTest},
    packages=['nativeconfig', 'nativeconfig.options', 'nativeconfig.configs'],
    tests_require=['pytest'],
)
