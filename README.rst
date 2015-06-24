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
        CONFIG_VERSION = __version__
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')
        age = IntOption('Age')

will store config in Registry on Windows, in NSUserDefaults on Mac OS X and in json-formatted file everywhere else.


Versioning
----------
The task that every developer is going to face. Fortunately nativeconfig has everything to assist you.
Each config is versioned and default to 1.0. Its version is stored in the config backend under the "ConfigVersion" name which
can be altered by modifying the CONFIG_VERSION_OPTION_NAME class variable.

You should override it in custom subclass by defining the CONFIG_VERSION variable. Value that usually makes most sense is the `__version__ <https://www.python.org/dev/peps/pep-0396/>`_ variable.
Each time config is instantiated the `migrate` method is called. Implementation of the base class simply updates value of the "ConfigVersion" (or whatever you called it) option to the actual value.
Reasonably, but insufficiently. Let's see what we can do:

.. code-block:: python
    class MyConfig(PreferredConfig):
        CONFIG_VERSION = __version__
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')

        def migrate(self, version):
            if version is None:
                # Either called for the very first time OR user's backed is broken because it lacks value of the ConfigVersion option.
                pass

            if version <= <newer version>:
                # Obviously <= will not work for strings. You should use your own comparison function that follows you versioning guidelines.
                pass

            if version <= <newest version>:
                # Version should be checked starting from the oldest to the current so you can gracefully migrate even the oldest user's config.
                # `if` is used instead of `elif` for the same reason: you may need to migrate user's data through multiple versions of the config file.
                pass

            if version <= <most recent version>:
                pass


            super().migrage(version)  # always call base class implementation at the end!


TL;DR three simple rules:

1. Check from the oldest to the newest version
2. User `if` instead of `elif`
3. Call super at the end


Tests
-----
To run tests, use the `python -m test` command.
