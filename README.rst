nativeconfig
============

.. image:: https://travis-ci.org/GreatFruitOmsk/nativeconfig.svg?branch=master

.. image:: https://badge.fury.io/py/nativeconfig.png
    :target: http://badge.fury.io/py/nativeconfig


Developers of cross-platform applications often face problems when they need to interact with the system.
Config files are no exception, since every popular OS has its own format and guidelines.

nativeconfig addresses this problem in an elegant and Pythonic way:

.. code-block:: python

    import os
    from nativeconfig import PreferredConfig, StringOption, IntOption

    class MyConfig(PreferredConfig):
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')
        
        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')
        age = IntOption('Age')

will store config in Registry on Windows, in NSUserDefaults on Mac OS X and in json-formatted file everywhere else.
