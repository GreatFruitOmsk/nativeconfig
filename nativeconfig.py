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
>>> MyConfig.instance().del_value_for_option_name('FavoriteNumber')
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import datetime
from functools import partial
import json
import logging
import os
import sys
import time
import threading


__version__ = '1.0.0'


LOG = logging.getLogger(__name__)


class Error(Exception):
    pass


class ValidationError(Error):
    def __init__(self, msg, value):
        self.value = value
        super().__init__(msg)


class SerializationError(Error):
    def __init__(self, msg, value):
        self.value = value
        super().__init__(msg)


class DeserializationError(Error):
    def __init__(self, msg, raw_value):
        self.raw_value = raw_value
        super().__init__(msg)


class BaseOption(property, metaclass=ABCMeta):
    """
    Base class that provides structure, flow and basic methods to work with options.

    An option must have a name and 4 methods:
    - getter to read raw value from Storage
    - setter to write value to Storage
    - deleter to delete value from Storage
    - resolver to resolve value that cannot be deserialized



    Value of an option can be overridden via an environment variable.

    Setting option to  None is equivalent to deleting it.

    @raise Error: Raise if choices is an empty list.
    @raise ValidationError: Raise if default value is invalid.
    """
    def __init__(self,
                 name,
                 getter='get_value',
                 setter='set_value',
                 deleter='del_value',
                 resolver='resolve_value',
                 choices=None,
                 env_name=None,
                 default=None,
                 default_if_empty=False):
        """
        @param name: Name of the property.
        @type name: str

        @param getter: Name of the method of the enclosing class to get value.

        @param setter: Name of the of the enclosing class to set value.

        @param deleter: Name of the deleter of the enclosing class to delete value.

        @param resolver: Name of the resolver of the enclosing class to resolve value that cannot be serialized.

        @param choices: List of allowed choices for the option.

        @param env_name: Name of the environment variable that can override value of the option
        @type env_name: str

        @param default: Default value of the option.

        @param default_if_empty: Whether default should be used when raw value is an empty string.
        @type default: bool

        @raise ValidationError: if default or any of choices is invalid.
        """
        super(BaseOption, self).__init__(self.fget, self.fset, self.fdel, doc=self.__doc__)

        self._name = name
        self._getter = getter
        self._setter = setter
        self._deleter = deleter
        self._resolver = resolver
        self._choices = choices
        self._env_name = env_name
        self._default = default
        self._default_if_empty = default_if_empty

        self._one_shot_value = None

        if not name:
            raise Error("name cannot be empty")

        if choices is not None and len(choices) == 0:
            raise Error("choices cannot be empty")

        if choices is not None:
            for c in choices:
                self.validate(c)

        if default is not None:
            self.validate(default)

    def validate(self, value):
        """
        Validate value. Must raise ValidationError if value is wrong.

        @raise ValidationError: Raise if value is wrong.
        """
        if value is None:
            return

        if self._choices is not None and value not in self._choices:
            raise ValidationError("value '{}' is not one of choices '{}'".format(value, self._choices), value)

    def serialize(self, value):
        """
        Serialize value to raw value.

        @see: deserialize

        @raise SerializationError: Raise if value cannot be serialized.
        """
        return str(value)

    def deserialize(self, raw_value):
        """
        Deserialize raw value to value.

        @see: serialize

        @raise DeserializationError: Raise if value cannot be deserialized.
        """
        return str(raw_value)

    def serialize_json(self, value):
        """
        Serialize value to json compatible string.

        @see: deserialize_json

        @rtype: str
        """
        return json.dumps(value)

    def deserialize_json(self, json_value):
        """
        Deserialize json value to value.

        @see: serialize_json
        """
        return json.loads(json_value)

    def set_one_shot_value(self, value):
        """
        Set one shot value of the option that overrides value from storage but can be reset by set.

        Useful if you want to allow a user to override the option via CLI.

        @raise ValidationError: Raise if value is not valid.
        """
        self.validate(value)
        self._one_shot_value = None

    def fget(self, enclosing_self):
        """
        @raise DeserializationError: Raise if value cannot be deserialized or deserialized value isn't one of choices.
        """
        raw_v = None

        if self._env_name:
            raw_v = os.getenv(self._env_name)
            if raw_v is not None:
                LOG.debug("value of '%s' is overridden by environment variable: %s", self._name, raw_v)

        if raw_v is None:
            raw_v = self._one_shot_value

        if raw_v is None:
            raw_v = getattr(enclosing_self, self._getter)(self._name)

        if raw_v is None or (self._default_if_empty and raw_v == ""):
            LOG.debug("No value is set for '%s', use default.", self._name)
            return self._default
        else:
            try:
                value = self.deserialize(raw_v)
                if self._choices and value not in self._choices:
                    raise DeserializationError("value '{}' is not one of choices {}".format(value, self._choices), value)
                else:
                    return value
            except DeserializationError as e:
                return getattr(enclosing_self, self._resolver)(e, self._name, raw_v)

    def fset(self, enclosing_self, value):
        self._one_shot_value = None

        if value is not None:
            self.validate(value)
            raw_value = self.serialize(value)
            LOG.debug("Value of '%s' is set to '%s'.", value, raw_value)
            getattr(enclosing_self, self._setter)(self._name, raw_value)
        else:
            self.fdel(enclosing_self)

    def fdel(self, enclosing_self):
        LOG.debug("Delete value of '%s'.", self._name)
        getattr(enclosing_self, self._deleter)(self._name)


class BooleanOption(BaseOption):
    TRUE_VALUES = ['1', 'YES', 'TRUE', 'ON']
    FALSE_VALUES = ['0', 'NO', 'FALSE', 'OFF']
    ALLOWED_VALUES = TRUE_VALUES + FALSE_VALUES

    def __init__(self,
                 name,
                 getter='get_value',
                 setter='set_value',
                 deleter='del_value',
                 resolver='resolve_value',
                 env_name=None,
                 default=None):
        super().__init__(name, getter, setter, deleter, resolver, env_name=env_name, default=default,
                         default_if_empty=True)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, bool):
            raise ValidationError("Only boolean values are allowed.", value)

    def serialize(self, value):
        return '1' if value else '0'

    def deserialize(self, raw_value):
        if raw_value.upper() in self.TRUE_VALUES:
            return True
        elif raw_value.upper() in self.FALSE_VALUES:
            return False
        else:
            raise DeserializationError("value '{}' must be one of {}.".format(raw_value, self.ALLOWED_VALUES), raw_value)


class CharOption(BaseOption):
    pass


class DateOption(BaseOption):
    def __init__(self,
                 name,
                 getter='get_value',
                 setter='set_value',
                 deleter='del_value',
                 resolver='resolve_value',
                 choices=None,
                 env_name=None,
                 default=None):
        super().__init__(name, getter, setter, deleter, resolver, choices=choices, env_name=env_name, default=default,
                         default_if_empty=True)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, datetime.date):
            raise ValidationError("Only datetime.date values are allowed.", value)

    def serialize(self, value):
        return value.isoformat()

    def deserialize(self, raw_value):
        try:
            t = time.strptime(raw_value, '%Y-%m-%d')
            return datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
        except ValueError:
            raise DeserializationError("Date must be of the YYYY-MM-DD format.", raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


class DateTimeOption(BaseOption):
    pass


class EmailOption(BaseOption):
    pass


class FilePathOption(BaseOption):
    pass


class FloatOption(BaseOption):
    pass


class IntegerOption(BaseOption):
    def __init__(self, name, getter, setter, deleter, allowed_range=None, choices=None, env_name=None, default=None):
        if allowed_range is not None and choices is not None:
            raise Error("both range and choices cannot be None simultaneously")

        self._range = allowed_range
        super().__init__(name, getter, setter, deleter, choices, env_name=env_name, default=default, default_if_empty=True)


class IPAddressOption(BaseOption):
    pass


class IPInterfaceOption(BaseOption):
    pass


class IPPortOption(BaseOption):
    pass


class TimeOption(BaseOption):
    pass


class URLOption(BaseOption):
    pass


class BaseConfig(metaclass=ABCMeta):
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

#{ Access options by name

    def get_value_for_option_name(self, name):
        """
        Get option's raw value by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str

        @return: JSON-encoded raw value. None if such option does not exist.
        @rtype: str or dict or list or None
        """
        attribute = self.property_for_option_name(name)

        if not attribute:
            return None

        return attribute.serialize_json(attribute.fget(self))

    def set_value_for_option_name(self, name, value):
        """
        Set option by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str

        @param value: JSON-encoded raw value.
        @type value: str
        """
        attribute = self.property_for_option_name(name)

        if attribute is None:
            return

        attribute.fset(self, attribute.deserialize_json(value))

    def del_value_for_option_name(self, name):
        """
        Delete option by its name in underlying config storage.

        @param name: Name of the option.
        @type name: str
        """
        attribute = self.property_for_option_name(name)

        if attribute is None:
            return

        attribute.fdel(self)

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

#{ Introspection

    def property_for_option_name(self, name):
        """
        Return property object for an option name. Useful for introspection.

        @param name: Name of an option.
        @type name: str

        @rtype: BaseOption or None
        """
        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, BaseOption) and attribute._name == name:
                return attribute
        else:
            return None

#{ Methods for subclasses

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
    def del_value(self, key):
        """
        Remove value for a given key.

        @param key: Key used to query value.
        @type key: str
        """
        pass

    def resolve_value(self, exception, key, raw_value):
        """
        Resolve raw value that cannot be deserialized or re-raise exception.

        Logs error message and returns default.

        @param exception: Exception that was raised during serialization.
        @type exception: DeserializationError

        @param key: Name of the option that cannot be deserialized.
        @type key: str

        @param raw_value: Raw value that cannot be deserialized.
        @type raw_value: str

        @return: Value to be used based on raw value.
        """
        LOG.error("Unable to deserialize value of '%s' from '%s': %s.", key, raw_value, exception)
        return self.property_for_option_name(key)._default

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
#}


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

        def del_value(self, key):
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

        def del_value(self, key):
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

    def del_value(self, key):
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

    def del_value(self, key):
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
