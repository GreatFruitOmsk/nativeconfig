import os
from setuptools import setup
from sys import platform


with open(os.path.join(os.path.dirname(__file__), 'nativeconfig', 'version.py')) as f:
    VERSION = None
    code = compile(f.read(), 'version.py', 'exec')
    exec(code)
    assert VERSION


setup(
    version=VERSION,
    packages=['nativeconfig', 'nativeconfig.options', 'nativeconfig.configs'],
    keywords='config',
    test_suite='test'
)
