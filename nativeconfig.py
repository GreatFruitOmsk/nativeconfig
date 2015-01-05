"""
The appconfig module provides convenient classes for developers of desktop applications to store user's config.

The PreferredConfig class is conveniently set to the most appropriate implementation depending on the system.
In particular, PreferredConfig resolves to:
- Windows: RegistryConfig
- Mac OS X: NSUserDefaultsConfig
- Linux: JSONConfig
- Everywhere else: InMemoryConfig

To define custom config class, you should first subclass desired base class and set its required properties:
>>> class MyConfig(RegistryConfig):
>>>     REGISTRY_PATH = r'Software\MyApp'
or
>>> class MyConfig(NSUserDefaultsConfig):
>>>     pass
or
>>> class MyConfig(JSONConfig):
>>>     JSON_PATH = '~/.config/MyApp/config'
or
>>> class MyConfig(PreferredConfig):
>>>     REGISTRY_PATH = r'Software\MyApp'
>>>     JSON_PATH = '~/.config/MyApp/config'
Note that when class is inherited from PreferredConfig all the required properties must be set since we should
support all possible resolutions.

The total list of available properties:
- LOG: Instance of a logger that is used for internal logging (optional).
- CREATE_IF_NEEDED: Whether path or registry key needs to be created if does not exist (optional).
- REGISTRY_KEY: Registry key such as HKEY_CURRENT_USER. See winreg docs. (optional)
- REGISTRY_PATH: Registry path relative to REGISTRY_KEY such as r'Software\MyApp'
- JSON_PATH: Path to the file.
- NSUSERDEFAULTS_SUITE: See NSUserDefaults documentation (optional).

To define custom config options use the *Option functions:
>>> class MyConfig(PreferredConfig):
>>>     REGISTRY_KEY = winreg.HKEY_CURRENT_USER
>>>     REGISTRY_PATH = r'Software\MyApp'
>>>     JSON_PATH = '~/.config/MyApp/config'
>>>
>>>     username = Option('Username', doc="Name of the user.")
>>>     sex = ChoiceOption('Sex', ['male', 'female'])
>>>     favorite_colors = ArrayOption('FavoriteColors', doc="User's favorite colors.")
>>>     most_visited_websites = DictOption('MistVisitedWebsites', doc="Track user for PRISM.")
The first argument passed to the *Option function is name of the option in underlying storage.

All options are normal Python properties with getter and setter:
>>> c = MyConfig.instance()
>>>
>>> print(c.username)
>>>
>>> c.sex = 'female'
>>>
>>> a = c.favorite_colors
>>> a.append('blue')
>>> c.favorite_colors = a
>>>
>>> d = c.most_visited_websites
>>> d['https://news.ycombinator.com/'] = 42
>>> c.most_visited_websites = d
>>>
>>> del c.favorite_colors
>>> c.most_visited_websites = None
Note that Array and Dict options cannot be update in place. Deleting the property is equivalent to setting
its value to None and will simply remove option from the config.

When option is about to be stored it is serialized. When it's about to be loaded it's deserialized. Both defaults to str
but can be easily configured:
>>> class MyConfig(PreferredConfig):
>>>     REGISTRY_KEY = winreg.HKEY_CURRENT_USER
>>>     REGISTRY_PATH = r'Software\MyApp'
>>>     JSON_PATH = '~/.config/MyApp/config'
>>>
>>>     favorite_number = Option('FavoriteNumber', default=9000, deserializer=int)
Note that serializer MUST return either a string or an object that provides
appropriate magic methods for conversion.

You can use your own types for deserialization:
>>> class Resolution:
>>>     DEFAULT_WIDTH = 1280
>>>     DEFAULT_HEIGHT = 800
>>>
>>>     def __init__(self, serialized_value=None):
>>>        if serialized_value is not None:
>>>            resolution = serialized_value.split('x', 2)
>>>
>>>            if len(resolution) == 2:
>>>                self._width = int(resolution[0]) if int(resolution[0]) > 0 else self.DEFAULT_WIDTH
>>>                self._height = int(resolution[1]) if int(resolution[1]) > 0 else self.DEFAULT_HEIGHT
>>>            else:
>>>                raise ValueError("Invalid format. Must be '<WIDTH>x<HEIGHT>'")
>>>        else:
>>>            self._width = self.DEFAULT_WIDTH
>>>            self._height = self.DEFAULT_HEIGHT
>>>
>>>     @property
>>>     def width(self):
>>>         return self._width
>>>
>>>     @property
>>>     def height(self):
>>>         return self._height
>>>
>>>     def __str__(self):
>>>         return '{:d}x{:d}'.format(self._width, self._height)
>>>
>>>
>>> class MyConfig(PreferredConfig):
>>>     REGISTRY_KEY = winreg.HKEY_CURRENT_USER
>>>     REGISTRY_PATH = r'Software\MyApp'
>>>     JSON_PATH = '~/.config/MyApp/config'
>>>
>>>     window_resolution = Option('Resolution', default=Resolution(), default_if_empty=True, deserializer=Resolution)
Note the default_if_empty argument: if due to some bug or user's manual misconfiguration value is set
to an empty string, default will be returned.
Since Resolution defines the __str__ method, default serializer (str) is fine.

nativeconfig also allows you to manage config from CLI. These functions mimics python properties but works
with raw names instead. The values they return/accept are JSON encoded version of a raw value:
>>> class MyConfig(PreferredConfig):
>>>     REGISTRY_KEY = winreg.HKEY_CURRENT_USER
>>>     REGISTRY_PATH = r'Software\MyApp'
>>>     JSON_PATH = '~/.config/MyApp/config'
>>>
>>>     favorite_number = Option('FavoriteNumber', default=9000, deserializer=int)
>>>
>>> MyConfig.instance().get_value_for_option_name('FavoriteNumber') # '"9000"'
>>> MyConfig.instance().set_value_for_option_name('FavoriteNumber', '"42"')
>>> MyConfig.instance().remove_value_for_option_name('FavoriteNumber')
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
from functools import partial
import json
import logging
import os
import sys
import threading


__version__ = '1.0'


LOG = logging.getLogger(__name__)


if sys.version_info < (3, 0):
    str = unicode


def Option(name, serializer=str, deserializer=str, default=None, default_if_empty=False, doc=""):
    """
    Generic method to add single-value options.

    @param name: Name of the option.
    @type name: str

    @param serializer: Callable that will be used to convert python object into string.

    @param deserializer: Callable that will be used to convert string into python object.

    @param default: Default value of the option.

    @param default_if_empty: If True, will return default if raw value is an empty string.
    @type default_if_empty: bool

    @param doc: Help message of the option.
    @type doc: str

    @rtype: property
    """
    def get_property(self, name, default, default_if_empty, deserializer, getter):
        raw_v = getattr(self, getter)(name)

        if raw_v is None or (default_if_empty and not raw_v):
            return default
        else:
            return deserializer(raw_v)

    def set_property(self, value, name, serializer, setter, deleter):
        if value is not None:
            getattr(self, setter)(name, serializer(value))
        else:
            getattr(self, deleter)(name)

    def del_property(self, name, deleter):
        getattr(self, deleter)(name)

    return property(partial(get_property, name=name, default=default, default_if_empty=default_if_empty, deserializer=deserializer, getter='get_value'),
                    partial(set_property, name=name, serializer=serializer, setter='set_value', deleter='remove_value'),
                    partial(del_property, name=name, deleter='remove_value'),
                    doc)


def IntOption(name, default=None, doc=""):
    return Option(name, lambda x: str(int(x)), int, default, True, doc)


def ChoiceOption(name, options, default, serializer=str, deserializer=str, doc=""):
    """
    Similar to Option but checks whether value is one of allowed.
    Default must present.

    @param name: Name of the option.
    @type name: str

    @param options: List of allowed values. Each value is an str.

    @param serializer: Callable that will be used to convert python object into string.

    @param deserializer: Callable that will be used to convert string into python object.

    @param default: Default value of the option.

    @param doc: Help message of the option.
    @type doc: str

    @rtype: property
    """
    if default not in options:
        raise ValueError("{} is not one of {}.".format(default, options))

    def get_property(self, name, default, deserializer, getter):
        raw_v = getattr(self, getter)(name)

        if not raw_v:
            return default
        else:
            return deserializer(raw_v)

    def set_property(self, value, name, options, serializer, setter, deleter):
        if value is not None:
            if value not in options:
                raise ValueError("{} is not one of {}.".format(value, options))

            getattr(self, setter)(name, serializer(value))
        else:
            getattr(self, deleter)(name)

    def del_property(self, name, deleter):
        getattr(self, deleter)(name)

    return property(partial(get_property, name=name, default=default, deserializer=deserializer, getter='get_value'),
                    partial(set_property, name=name, options=options, serializer=serializer, setter='set_value', deleter='remove_value'),
                    partial(del_property, name=name, deleter='remove_value'),
                    doc)


def DictOption(name, serializer=str, deserializer=str, default=None, doc=""):
    """
    Generic method to add dictionary options.

    @param name: Name of the option.
    @type name: str

    @param serializer: Callable that will be used to convert each value of the dictionary into str.

    @param deserializer: Callable that will be used to convert each value of the dictionary into python object.

    @param default: Default value of the option.

    @param doc: Help message of the option.
    @type doc: str

    @rtype: property
    """
    def get_property(self, name, default, deserializer, getter):
        raw_v = getattr(self, getter)(name)

        if raw_v is None:
            return default
        else:
            return {k: deserializer(v) for k, v in raw_v.items()}

    def set_property(self, value, name, serializer, setter, deleter):
        if value is not None:
            getattr(self, setter)(name, {k: serializer(v) for k, v in value.items()})
        else:
            getattr(self, deleter)(name)

    def del_property(self, name, deleter):
        getattr(self, deleter)(name)

    return property(partial(get_property, name=name, default=default, deserializer=deserializer, getter='get_dict_value'),
                    partial(set_property, name=name, serializer=serializer, setter='set_dict_value', deleter='remove_value'),
                    partial(del_property, name=name, deleter='remove_value'),
                    doc)


def ArrayOption(name, serializer=str, deserializer=str, default=None, doc=""):
    """
    Generic method to add array options.

    @param name: Name of the option.
    @type name: str

    @param serializer: Callable that will be used to convert each value of the array into str.

    @param deserializer: Callable that will be used to convert each value of the array into python object.

    @param default: Default value of the option.

    @param doc: Help message of the option.
    @type doc: str

    @rtype: property
    """
    def get_property(self, name, default, deserializer, getter):
        raw_v = getattr(self, getter)(name)

        if raw_v is None:
            return default
        else:
            return [deserializer(value) for value in raw_v]

    def set_property(self, value, name, serializer, setter, deleter):
        if value is not None:
            getattr(self, setter)(name, [serializer(value) for value in value])
        else:
            getattr(self, deleter)(name)

    def del_property(self, name, deleter):
        getattr(self, deleter)(name)

    return property(partial(get_property, name=name, default=default, deserializer=deserializer, getter='get_array_value'),
                    partial(set_property, name=name, serializer=serializer, setter='set_array_value', deleter='remove_value'),
                    partial(del_property, name=name, deleter='remove_value'),
                    doc)


def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper


@add_metaclass(ABCMeta)
class BaseConfig(object):
    """
    Base class for all configs. Provides abstract methods and basic implementations.

    @cvar CREATE_IF_NEEDED: Whether entity to store config needs to be created if does not exist.
    """
    CREATE_IF_NEEDED = True

    _instances = {}
    _instances_events = {}
    _instances_lock = threading.Lock()

    @classmethod
    def instance(cls):
        with cls._instances_lock:
            instance_event = cls._instances_events.get(cls, threading.Event())

            if not instance_event.is_set():
                try:
                    cls._instances[cls] = cls()
                finally:
                    instance_event.set()
                    cls._instances_events[cls] = instance_event

        return cls._instances.get(cls, None)

    @classmethod
    def validate(cls):
        """
        Validate config options.

        @raise AttributeError: Raised if properties are duplicated.
        """
        properties = set()

        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)

            if isinstance(attribute, property) and hasattr(attribute.fget, 'keywords'):
                property_name = attribute.fget.keywords['name']

                if property_name in properties:
                    raise AttributeError("Duplication of property named {}!".format(property_name))
                else:
                    properties.add(property_name)

    def get_value_for_option_name(self, name):
        """
        Get option's raw value by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str

        @return: JSON-encoded raw value. None if such option does not exist.
        @rtype: str or dict or list or None
        """
        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, property) and hasattr(attribute.fget, 'keywords') and attribute.fget.keywords['name'] == name:
                getter = attribute.fget.keywords['getter']
                value = getattr(self, getter)(name)
                if value is None or (value == '' and attribute.fget.keywords.get('default_if_empty', False)):
                    default = attribute.fget.keywords['default']
                    if default is not None:
                        # We only support 3 types of values: str, dict and list. All 3 has predefined getters and setter.
                        if getter == 'get_array_value':
                            value = [attribute.fset.keywords['serializer'](v) for v in default]
                        elif getter == 'get_dict_value':
                            value = {k: attribute.fset.keywords['serializer'](v) for k, v in default.items()}
                        else:
                            value = attribute.fset.keywords['serializer'](default)
                    else:
                        value = None

                return json.dumps(value)
        else:
            return None

    def set_value_for_option_name(self, name, value):
        """
        Set option by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str

        @param value: JSON-encoded raw value.
        @type value: str
        """
        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, property) and hasattr(attribute.fget, 'keywords') and attribute.fget.keywords['name'] == name:
                value = json.loads(value)
                if value is not None:
                    serializer = attribute.fset.keywords['serializer']
                    deserializer = attribute.fget.keywords['deserializer']
                    # Ensure input is valid.
                    if isinstance(value, list):
                        value = [serializer(deserializer(v)) for v in value]
                    elif isinstance(value, dict):
                        value = {k: serializer(deserializer(v)) for k, v in value.items()}
                    else:
                        value = serializer(deserializer(value))
                    getattr(self, attribute.fset.keywords['setter'])(name, value)
                else:
                    getattr(self, attribute.fset.keywords['deleter'])(name, value)
                break

    def remove_value_for_option_name(self, name):
        """
        Delete option by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str
        """
        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, property) and hasattr(attribute.fget, 'keywords') and attribute.fget.keywords['name'] == name:
                delattr(self, attribute_name)
                break

    def snapshot(self):
        """
        Get snapshot of current config.

        @return: Dict of option: value format.
        @rtype: dict
        """
        options = {}

        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, property) and hasattr(attribute.fget, 'keywords'):
                name = attribute.fget.keywords['name']
                options[name] = self.get_value_for_option_name(name)

        return options

    @abstractmethod
    def get_value(self, key):
        """
        Return raw value for a given key or None if no value exist and default should be used.

        @param key: Key used to query value.
        @type key: str

        @rtype: str or None
        """
        pass

    @abstractmethod
    def set_value(self, key, value):
        """
        Set new value for a given key.

        @param key: Key used to query value.
        @type key: str

        @param value: Value to set. Must be serialized.
        @type value: str
        """
        pass

    @abstractmethod
    def remove_value(self, key):
        """
        Remove value for a given key.

        @param key: Key used to query value.
        @type key: str
        """
        pass

    @abstractmethod
    def get_array_value(self, key):
        """
        Return an array of raw values for a given key.

        @param key: Key used to query value.
        @type key: str

        @rtype: list or None
        """
        pass

    @abstractmethod
    def set_array_value(self, key, value):
        """
        Set new value for a given key.

        @param key: Key used to query value.
        @type key: str

        @param value:  Value to set. Must be a list of serialized values.
        @type value: list
        """
        pass

    @abstractmethod
    def get_dict_value(self, key):
        """
        Return a dict of raw values for a given key.

        @param key: Key used to query value.
        @type key: str

        @rtype: dict or None
        """
        pass

    @abstractmethod
    def set_dict_value(self, key, value):
        """
        Set new value for a given key.

        @param key: Key used to query value.
        @type key: str

        @param value:  Value to set. Must be a dict of serialized values.
        @type value: dict
        """
        pass


if sys.platform.startswith('win32'):
    try:
        import winreg
    except ImportError:
        import _winreg as winreg

    ERROR_NO_MORE_ITEMS = 259
    ERROR_NO_MORE_FILES = 18

    def _traverse_registry_key(key, sub_key):
        """
        Traverse registry key and yield one by one.

        @raise WindowsError: If key cannot be opened (e.g. does not exist).
        """
        current_key = winreg.OpenKey(key, sub_key, 0, winreg.KEY_ALL_ACCESS)

        try:
            i = 0
            while True:
                next_key = winreg.EnumKey(current_key, i)
                for k in _traverse_registry_key(key, r'{}\{}'.format(sub_key, next_key)):
                    yield k
                i += 1
        except WindowsError:
            yield sub_key

    class RegistryConfig(BaseConfig):
        """
        @cvar REGISTRY_KEY: A registry key such as HKEY_CURRENT_USER. See winreg docs.
        @cvar REGISTRY_PATH: Path relative to REGISTRY_KEY.
        """
        LOG = LOG.getChild('RegistryConfig')
        REGISTRY_KEY = winreg.HKEY_CURRENT_USER
        REGISTRY_PATH = None

        def __init__(self):
            super(RegistryConfig, self).__init__()

            if self.CREATE_IF_NEEDED:
                k = winreg.CreateKey(self.REGISTRY_KEY, self.REGISTRY_PATH)
                winreg.CloseKey(k)

        def get_value(self, key):
            try:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH) as app_key:
                    try:
                        return str(winreg.QueryValueEx(app_key, key)[0])
                    except:
                        self.LOG.info("Unable to get '%s' from the registry:", key, exc_info=True)
            except:
                self.LOG.exception("Unable to access registry:")

            return None

        def set_value(self, key, value):
            try:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_WRITE) as app_key:
                    try:
                        winreg.SetValueEx(app_key, key, 0, winreg.REG_SZ, str(value))
                    except:
                        self.LOG.exception("Unable to set '%s' in the registry:", key)
            except:
                self.LOG.exception("Unable to access registry:")

        def remove_value(self, key):
            try:
                try:
                    for k in _traverse_registry_key(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, key)):
                        winreg.DeleteKey(self.REGISTRY_KEY, k)
                except WindowsError:
                    try:
                        with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as app_key:
                            winreg.DeleteValue(app_key, key)
                    except WindowsError:
                        self.LOG.info("Unable to delete '%s' from the registry:", key)
            except:
                self.LOG.exception("Unable to access registry:")

        def get_array_value(self, key):
            try:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH) as app_key:
                    try:
                        return [str(v) for v in winreg.QueryValueEx(app_key, key)[0]]
                    except:
                        self.LOG.info("Unable to get array '%s' from the registry:", key, exc_info=True)
            except:
                self.LOG.exception("Unable to access registry:")

            return None

        def set_array_value(self, key, value):
            try:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_WRITE) as app_key:
                    try:
                        winreg.SetValueEx(app_key, key, 0, winreg.REG_MULTI_SZ, [str(v) for v in value])
                    except:
                        self.LOG.exception("Unable to set array '%s' in the registry:", key)
            except:
                self.LOG.exception("Unable to access registry:")

        def get_dict_value(self, key):
            try:
                with winreg.OpenKey(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, key), 0, winreg.KEY_ALL_ACCESS) as app_key:
                    v = {}

                    try:
                        i = 0
                        while True:
                            name, value, _value_type = winreg.EnumValue(app_key, i)

                            if value is not None:
                                v[name] = str(value)

                            i += 1
                    except WindowsError as e:
                        if e.winerror != ERROR_NO_MORE_ITEMS and e.winerror != ERROR_NO_MORE_FILES:
                            raise
                        else:
                            pass  # end of keys
                    except:
                        self.LOG.exception("Error during registry enumeration:")
                        return None

                    return v
            except:
                self.LOG.info("Unable to get dict '%s' from the registry:")

            return None

        def set_dict_value(self, key, value):
            try:
                with winreg.CreateKey(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, key)) as dict_key:
                    try:
                        for k, v in value.items():
                            winreg.SetValueEx(dict_key, str(k), 0, winreg.REG_SZ, str(v))
                    except:
                        self.LOG.exception("Unable to access registry:")
            except:
                self.LOG.exception("Unable to access registry:")
elif sys.platform.startswith('darwin'):
    import objc

    class NSUserDefaultsConfig(BaseConfig):
        """
        @cvar NSUSERDEFAULTS_SUITE: Name of suite shared between different apps. See NSUserDefaults docs.
        """
        LOG = LOG.getChild('NSUserDefaultsConfig')
        NSUSERDEFAULTS_SUITE = None

        def __init__(self):
            super(NSUserDefaultsConfig, self).__init__()

            if self.NSUSERDEFAULTS_SUITE is not None:
                self._user_defaults = objc.lookUpClass('NSUserDefaults').alloc().initWithSuiteName_(self.NSUSERDEFAULTS_SUITE)
            else:
                self._user_defaults = objc.lookUpClass('NSUserDefaults').standardUserDefaults()

        def get_value(self, key):
            try:
                v = self._user_defaults.stringForKey_(key)
                return str(v) if v is not None else None
            except:
                self.LOG.info("Unable to get '%s' from the user defaults:", key, exc_info=True)

            return None

        def set_value(self, key, value):
            try:
                self._user_defaults.setObject_forKey_(str(value), key)
            except:
                self.LOG.exception("Unable to set '%s' in the user defaults:", key)

        def remove_value(self, key):
            try:
                self._user_defaults.removeObjectForKey_(key)
            except:
                self.LOG.exception("Unable to delete '%s' from the user defaults:", key)

        def get_array_value(self, key):
            try:
                v = self._user_defaults.arrayForKey_(key)
                return [str(i) for i in v] if v is not None else None
            except:
                self.LOG.info("Unable to get array '%s' from the user defaults:", key, exc_info=True)

            return None

        def set_array_value(self, key, value):
            try:
                self._user_defaults.setObject_forKey_([str(v) for v in value], key)
            except:
                self.LOG.exception("Unable to set array '%s' in the user defaults:", key)

        def get_dict_value(self, key):
            try:
                v = self._user_defaults.dictionaryForKey_(key)
                return {str(k): str(i) for k, i in v.items()} if v is not None else None
            except:
                self.LOG.info("Unable to get dict '%s' from the user defaults:", key, exc_info=True)

        def set_dict_value(self, key, value):
            try:
                self._user_defaults.setObject_forKey_({str(k): str(v) for k, v in value.items()}, key)
            except:
                self.LOG.exception("Unable to set dict '%s' in the user defaults:", key)


class JSONConfig(BaseConfig):
    """
    @cvar JSON_PATH: Path to a JSON file.
    """
    LOG = LOG.getChild('JSONConfig')
    JSON_PATH = None

    def __init__(self):
        if self.CREATE_IF_NEEDED and not os.path.isfile(self.JSON_PATH):
            with open(self.JSON_PATH, 'w+') as file:
                file.write(json.dumps({}))

    def _get_json_value(self, key):
        try:
            with open(self.JSON_PATH, 'r') as file:
                content = file.readline()
                try:
                    conf = json.loads(content)
                    if key in conf:
                        return conf[key]
                    else:
                        self.LOG.info("Config file doesn't contain the key '%s'.", key)
                except ValueError:
                    self.LOG.exception("Config file isn't valid:")
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    def _set_json_value(self, key, value):
        try:
            with open(self.JSON_PATH, 'r+') as file:
                content = file.readline()
                conf = json.loads(content)
                conf[key] = value
                conf_text = json.dumps(conf)
                file.seek(0)
                file.write(conf_text)
                file.truncate()
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    def get_value(self, key):
        v = self._get_json_value(key)
        return str(v) if v is not None else None

    def set_value(self, key, value):
        self._set_json_value(key, str(value))

    def remove_value(self, key):
        try:
            with open(self.JSON_PATH, 'r+') as file:
                content = file.readline()
                conf = json.loads(content)
                conf.pop(key, None)
                conf_text = json.dumps(conf)
                file.seek(0)
                file.write(conf_text)
                file.truncate()
        except:
            self.LOG.exception("Unable to access config file:")

    def get_array_value(self, key):
        v = self._get_json_value(key)
        return [str(i) for i in v] if v is not None else None

    def set_array_value(self, key, value):
        self._set_json_value(key, [str(v) for v in value])

    def get_dict_value(self, key):
        v = self._get_json_value(key)
        return {str(k): str(i) for k, i in v.items()} if v is not None else None

    def set_dict_value(self, key, value):
        self._set_json_value(key, {str(k): str(v) for k, v in value.items()})


class InMemoryConfig(BaseConfig):
    def __init__(self):
        super(InMemoryConfig, self).__init__()
        self._config = {}

    def get_value(self, key):
        v = self._config.get(key, None)
        return str(v) if v is not None else None

    def set_value(self, key, value):
        self._config[key] = str(value)

    def remove_value(self, key):
        self._config.pop(key, None)

    def get_array_value(self, key):
        v = self._config.get(key, None)
        return [str(i) for i in v] if v is not None else None

    def set_array_value(self, key, value):
        self._config[key] = [str(v) for v in value]

    def get_dict_value(self, key):
        v = self._config.get(key, None)
        return {str(k): str(i) for k, i in v.items()} if v is not None else None

    def set_dict_value(self, key, value):
        self._config[key] = {str(k): str(v) for k, v in value.items()}


if sys.platform.startswith('win32'):
    PreferredConfig = RegistryConfig
elif sys.platform.startswith('darwin'):
    PreferredConfig = NSUserDefaultsConfig
elif sys.platform.startswith('linux'):
    PreferredConfig = JSONConfig
else:
    PreferredConfig = InMemoryConfig
