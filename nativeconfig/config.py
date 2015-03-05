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
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
import threading


__version__ = '2.0.0'


LOG = logging.getLogger(__name__)


class CharOption(BaseOption):
    pass


class DateOption(BaseOption):
    def __init__(self, name, **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, datetime.date):
            raise ValidationError("Only datetime.date values are allowed.", value)

    def serialize(self, value):
        return value.isoformat()

    def deserialize(self, raw_value):
        try:
            return datetime.datetime.strptime(raw_value, '%Y-%m-%d').date()
        except ValueError:
            raise DeserializationError("Date must be of the YYYY-MM-DD format.", raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


# TODO: datetime option requires complicated handling of timezones which are not part of stdlib
# class DateTimeOption(BaseOption):
#     pass


# TODO: email option requires advanced validation
# class EmailOption(BaseOption):
#     pass

class PathOption(BaseOption):
    def __init__(self, name,  **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, Path):
            raise ValidationError("only Path values are allowed", value)

    def deserialize(self, raw_value):
        return Path(raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


class PureWindowsPathOption(BaseOption):
    def __init__(self, name,  **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, PureWindowsPath):
            raise ValidationError("only PureWindowsPath values are allowed", value)

    def deserialize(self, raw_value):
        return PureWindowsPath(raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


class PurePosixPathOption(BaseOption):
    def __init__(self, name,  **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, PurePosixPath):
            raise ValidationError("only PurePosixPath values are allowed", value)

    def deserialize(self, raw_value):
        return PurePosixPath(raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


class FloatOption(BaseOption):
    def __init__(self, name, **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, float) and not isinstance(value, int):
            raise ValidationError("only float and int values are allowed", value)

    def deserialize(self, raw_value):
        return float(raw_value)


class IntegerOption(BaseOption):
    def __init__(self, name, **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)
        if not isinstance(value, int):
            raise ValidationError("only int values are allowed", value)

    def deserialize(self, raw_value):
        return int(raw_value)


class IPAddressOption(BaseOption):
    pass


class IPInterfaceOption(BaseOption):
    pass


class IPPortOption(IntegerOption):
    def __init__(self, name, min_port=0, max_port=65536, **kwargs):
        super().__init__(name, choices=range(min_port, max_port), **kwargs)


class TimeOption(BaseOption):
    def __init__(self, name, **kwargs):
        super().__init__(name, default_if_empty=True, **kwargs)

    def validate(self, value):
        super().validate(value)

        if not isinstance(value, datetime.time):
            raise ValidationError("Only datetime.time values are allowed", value)

    def serialize(self, value):
        return value.isoformat()

    def deserialize(self, raw_value):
        try:
            try:
                return datetime.datetime.strptime(raw_value, '%H:%M:%S.%f%z').timetz()
            except ValueError:
                try:
                    return datetime.datetime.strptime(raw_value, '%H:%M:%S.%f').timetz()
                except ValueError:
                    try:
                        return datetime.datetime.strptime(raw_value, '%H:%M:%S%z').timetz()
                    except ValueError:
                        return datetime.datetime.strptime(raw_value, '%H:%M:%S').timetz()
        except ValueError:
            raise DeserializationError("time must be of the HH-MM-SS[.mmmmmm[(+|-)ZZZZ]] format.", raw_value)

    def serialize_json(self, value):
        return super().serialize_json(self.serialize(value))

    def deserialize_json(self, json_value):
        return self.deserialize(super().deserialize_json(json_value))


# TODO: url option requires advanced validation
# class URLOption(BaseOption):
#     pass




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





if sys.platform.startswith('win32'):
    PreferredConfig = RegistryConfig
elif sys.platform.startswith('darwin'):
    PreferredConfig = NSUserDefaultsConfig
elif sys.platform.startswith('linux'):
    PreferredConfig = JSONConfig
else:
    PreferredConfig = InMemoryConfig
