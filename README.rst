nativeconfig
============

.. image:: https://travis-ci.org/GreatFruitOmsk/nativeconfig.svg?branch=master

.. image:: https://badge.fury.io/py/nativeconfig.png
    :target: http://badge.fury.io/py/nativeconfig


Developers of cross-platform applications often face problems when they need to interact with the system.
Config files are no exception, since every popular OS has its own format and guidelines.

nativeconfig addresses this problem in an elegant and pythonic way:

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

will store config in Registry on Windows, in NSUserDefaults on Mac OS X (if the `pyobjc-core <https://pypi.python.org/pypi/pyobjc-core/3.0.4>`_ module is available) and in json-formatted file everywhere else.


Caching
-------
Implementations for all platforms support caching which minimizes access to the backend. Specifically value is only read if it's not known to cache
and written if it's different than cached one.

Simply declare your subclass with `ALLOW_CACHE` set to `True`:

.. code-block:: python

    class MyConfig(PreferredConfig):
        CONFIG_VERSION = __version__
        ALLOW_CACHE = True
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')

You can also set this settings per option, by declarding them with `allow_cache` set to `True`.


JSON as a universal format
--------------------------
At some point you will need to provide public interface (e.g. CLI or API) to edit config of your application.
For this reason there are methods to convert each option individually or whole config into JSON:

.. code-block:: python

    class MyConfig(PreferredConfig):
        CONFIG_VERSION = __version__
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')

    MyConfig.get_instance().get_value_for_option_name('FirstName')  # will return JSON version of first_name's value
    MyConfig.get_instance().snapshot()  # will return a JSON dictionary of all options
    MyConfig.get_instance().restore_snapshot(user_edited_snapshot)  # will update options with from user-edited JSON


Introspection
-------------
It's always cool when you hack around possible flaws in lib's code. So you have it: API of BasicConfig and BasicOption is carefully designed to be hackable.
In particular, config's attibutes can be easily inspected via the set of methods grouped under "Introspection" section or by playing with the BasicConfig._ordered_options
directly. You didn't misread, options are already are ordered in order of definition and even subclassing and even overriding!

.. code-block:: python

    class MyConfig(PreferredConfig):
        CONFIG_VERSION = __version__
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')

    MyConfig.get_instance().get_value_for_option_name('FirstName')  # will return python value of the FirstName option
    MyConfig.get_instance().get_raw_value_for_option_name('FirstName')  # will return raw value of the FirstName option
    MyConfig.get_instance().get_json_value_for_option_name('FirstName')  # will return JSON encoded value of the FirstName option



Versioning
----------
The task that every developer is going to face. Fortunately nativeconfig has everything to assist you!

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


            super().migrate(version)  # always call base class implementation at the end!


TL;DR three simple rules:

1. Check from the oldest to the newest version
2. User `if` instead of `elif`
3. Call super at the end


Error Recovery
--------------
When user base is huge, all sorts of weird issues will happen. Unexpected values of options is probably the most common one.
And nativeconfig has everything you need to recover from such errors!

Whenever config is unable to deserialize value or if deserialized value is unexpected (e.g. you wanted float bug got a path)
the `resolve_value` method is called. Default implementation logs an error and returns a default. If that's not sufficient
or you have a better idea of how to recover than using default, you should override this method:

.. code-block:: python

    class MyConfig(PreferredConfig):
        CONFIG_VERSION = __version__
        REGISTRY_PATH = r'Software\MyApp'
        JSON_PATH = os.path.expanduser('~/.config/MyApp/config')

        first_name = StringOption('FirstName')
        last_name = StringOption('LastName')

        def resolve_value(self, exc_info, name, raw_or_json_value, source):
            if name == 'FirstName':
                # E.g. restore value from Cloud-stored credentials.
                pass

Pretty basic: you have exc_info extracted where problem happened (either ValidationError or DeserializationError), name of the option, raw or json value and
source that explains where error happened.


Debugging
---------
The `warn` module is used in some places, so you're advised to debug your app by turning all warnings into errors as described in `docs <https://docs.python.org/library/warnings.html>`_.
Various logs are written to the `nativeconfig` logger. You can increase verbosity by advancing the level.


Testing
-------
To run tests, use the `python -m test` command.
