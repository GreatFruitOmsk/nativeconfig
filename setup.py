import os
from setuptools import setup
from sys import platform


with open(os.path.join(os.path.dirname(__file__), 'nativeconfig', 'version.py')) as f:
    VERSION = None
    code = compile(f.read(), 'version.py', 'exec')
    exec(code)
    assert VERSION


setup(
    name='nativeconfig',
    version=VERSION,
    packages=['nativeconfig', 'nativeconfig.options', 'nativeconfig.config'],
    url='https://github.com/GreatFruitOmsk/nativeconfig',
    license='MIT License',
    author='Ilya Kulakov',
    author_email='kulakov.ilya@gmail.com',
    description="Cross-platform python module to store application config via native subsystems such as Windows Registry or NSUserDefaults.",
    platforms=["Mac OS X 10.6+", "Windows XP+", "Linux 2.6+"],
    keywords='config',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    test_suite='test'
)
