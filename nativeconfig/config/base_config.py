from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import contextlib
import inspect
import json
import logging
import threading
import traceback
from warnings import warn

from nativeconfig.options.base_option import BaseOption
from nativeconfig.options import StringOption


LOG = logging.getLogger('nativeconfig')


class _OrderedClass(ABCMeta):
    """
    Simple metaclass that maintains list of all properties (including all superclasses) in order of definition.
    """
    @classmethod
    def __prepare__(metacls, name, bases):
        return OrderedDict()

    def __new__(cls, name, bases, classdict):
        result = type.__new__(cls, name, bases, dict(classdict))
        result._ordered_options = []

        def add_option(base_class, option):
            for i, o in enumerate(result._ordered_options):
                if o.name == option.name:
                    if not issubclass(option.__class__, o.__class__):
                        warn("Type (\"{}\") of the \"{}\" option overridden by \"{}\" is different than type (\"{}\") defined by one of super classes.".format(option.__class__.__name__, option.name, base_class.__name__, o.__class__.__name__))
                    result._ordered_options.pop(i)
                    break
            result._ordered_options.append(option)

        # Get ordered options from base class.
        mro = inspect.getmro(result)
        if len(mro) > 1:
            for base_class in reversed(mro[1:]):

                if hasattr(base_class, '_ordered_options'):
                    options = base_class._ordered_options
                else:  # e.g. mixin
                    options = [o for k, o in base_class.__dict__.items() if isinstance(o, BaseOption)]

                for o in options:
                    add_option(base_class, o)

        new_options = [v for k, v in classdict.items() if inspect.isdatadescriptor(v) and isinstance(v, BaseOption)]
        for o in new_options:
            add_option(result, o)

        return result


class BaseConfig(metaclass=_OrderedClass):
    """
    Base class for all configs.

    Methods that work with options by name does not fail explicitly but use warnings.warn

    Back end can be accessed by 2 groups of methods: thread safe and lock free. Context management
    is also implemented so you can lock once for multiple accesses.

    @cvar ALLOW_CACHE: Whether options by default will allow cache.
    @cvar CONFIG_VERSION: Version of the config. Used during migrations and usually should be identical to app's __version__.
    @cvar CONFIG_VERSION_OPTION_NAME: Name of the option that represents config version in backend.

    @ivar _ordered_options: Ordered dict of options defined in the order of definition from base class to subclasses.
    """
    ALLOW_CACHE = False
    CONFIG_VERSION = '1.0'
    CONFIG_VERSION_OPTION_NAME = "ConfigVersion"

    _instances = {}
    _instances_events = {}
    _instances_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        """
        Return singleton for current config subclass.

        @rtype: type(cls)
        """
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

        for attribute_name, attribute_value in inspect.getmembers(cls, inspect.isdatadescriptor):
            if isinstance(attribute_value, BaseOption):
                if attribute_value.name in properties:
                    raise AttributeError("Duplication of option named \"{}\"!".format(attribute_value.name))
                else:
                    properties.add(attribute_value.name)

    def __init__(self):
        self.validate()
        super().__init__()

        self._lock = threading.Lock()
        self._cache = self.reset_cache()

        self.migrate(self.config_version)

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        with contextlib.suppress(RuntimeError):
            self._lock.release()

    #{ Default options

    config_version = StringOption(CONFIG_VERSION_OPTION_NAME, default=CONFIG_VERSION, doc="Version of the config.")

    #{ Access options by name

    def get_value_for_option_name(self, name):
        """
        Get option's Python Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @rtype: str or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.fget(self)
        else:
            warn("No option named \"{}\".".format(name))
            return None

    def get_raw_value_for_option_name(self, name):
        """
        Get option's Raw Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @rtype: str or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.serialize(attribute.fget(self))
        else:
            warn("No option named \"{}\".".format(name))
            return None

    def get_json_value_for_option_name(self, name):
        """
        Get option's JSON Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @rtype: str or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.serialize_json(attribute.fget(self))
        else:
            warn("No option named \"{}\".".format(name))
            return None

    def set_value_for_option_name(self, name, python_value):
        """
        Set option's Raw Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @param python_value: Python Value.
        @type python_value: object or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.fset(self, python_value)
        else:
            warn("No option named \"{}\".".format(name))

    def set_raw_value_for_option_name(self, name, raw_value):
        """
        Set option's Raw Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @param raw_value: Raw Value.
        @type raw_value: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.fset(self, attribute.deserialize(raw_value))
        else:
            warn("No option named \"{}\".".format(name))

    def set_json_value_for_option_name(self, name, json_value):
        """
        Set option's JSON Value by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str or None

        @param json_value: JSON Value. If 'null', value will be deleted.
        @type json_value: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.fset(self, attribute.deserialize_json(json_value))
        else:
            warn("No option named \"{}\".".format(name))

    def set_one_shot_value_for_option_name(self, name, python_value):
        """
        Set One Shot Value for a given name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @param python_value: Python Value.
        @type python_value: object or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.set_one_shot_value(python_value)
        else:
            warn("No option named \"{}\".".format(name))

    def set_one_shot_raw_value_for_option_name(self, name, raw_value):
        """
        Set One Shot Value for a given name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @param raw_value: Raw Value.
        @type raw_value: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.set_one_shot_value(attribute.deserialize(raw_value))
        else:
            warn("No option named \"{}\".".format(name))

    def set_one_shot_json_value_for_option_name(self, name, json_value):
        """
        Set One Shot Value for a given name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str

        @param json_value: JSON Value.
        @type json_value: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.set_one_shot_value(attribute.deserialize_json(json_value))
        else:
            warn("No option named \"{}\".".format(name))

    def del_value_for_option_name(self, name):
        """
        Delete option by its name.

        Issues a warning if option with a given name does not exist.

        @param name: Name of the option.
        @type name: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            attribute.fdel(self)
        else:
            warn("No option named \"{}\".".format(name))

    def validate_value_for_option_name(self, name, python_value):
        """
        Validate Python Value for an option with a given name.

        @param name: Name of the option.
        @type name: str

        @param python_value: Python Value.
        @type python_value: object or None

        @raise ValidationError: Raised if value is invalid.
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.validate(python_value)
        else:
            warn("No option named \"{}\".".format(name))

    def validate_raw_value_for_option_name(self, name, raw_value):
        """
        Validate Raw Value for an option with a given name.

        @param name: Name of the option.
        @type name: str

        @param raw_value: Raw Value.
        @type raw_value: str

        @raise ValidationError: Raised if value is invalid.
        @raise DeserializationError: Raised if value cannot be deserialized.
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.validate(attribute.deserialize(raw_value))
        else:
            warn("No option named \"{}\".".format(name))

    def validate_json_value_for_option_name(self, name, json_value):
        """
        Validate Raw Value for an option with a given name.

        @param name: Name of the option.
        @type name: str

        @param json_value: JSON Value.
        @type json_value: str

        @raise ValidationError: Raised if value is invalid.
        @raise DeserializationError: Raised if value cannot be deserialized.
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.validate(attribute.deserialize_json(json_value))
        else:
            warn("No option named \"{}\".".format(name))

    #{ Enumeration

    def options(self):
        """
        Generator to enumerate option names.
        """
        for o in self._ordered_options:
            yield o

    def items(self):
        """
        Generator to enumerate options and their Python Values.

        Yields option name, Python Value and value's source.
        """
        for o in self.options():
            python_value, source = o.read_value(self)
            yield o.name, python_value, source

    def raw_items(self):
        """
        Generator to enumerate options and their Raw Values.

        Yields option name, Raw Value and value's source.
        """
        for o in self.options():
            python_value, source = o.read_value(self)
            yield o.name, o.serialize(python_value), source

    def json_items(self):
        """
        Generator to enumerate options and their JSON Values.

        Yields option name, JSON Value and value's source.
        """
        for o in self.options():
            python_value, source = o.read_value(self)
            yield o.name, o.serialize_json(python_value), source

    #{ Snapshots

    def snapshot(self):
        """
        Get snapshot of current config.

        @return: Ordered JSON dict of json-serialized options.
        @rtype: str
        """
        return '{' + ', '.join(['{}: {}'.format(json.dumps(o.name), o.serialize_json(o.fget(self))) for o in self.options()]) + '}'

    def restore_snapshot(self, snapshot):
        """
        Set config values for older snapshot.

        If option represented in snapshot does not exist, warning will be raised.

        @param snapshot: Snapshot as returned by BaseConfig.snapshot
        """
        for k, v in json.loads(snapshot).items():
            # Additional quotes are needed, because values will be loaded into python strings,
            # but set_value_for_option_name expects JSON.
            self.set_json_value_for_option_name(k, json.dumps(v))

    #{ Introspection

    def option_for_name(self, name):
        """
        Return option (property object) for name.

        @param name: Name of an option.
        @type name: str

        @rtype: BaseOption or None
        """
        for o in self.options():
            if o.name == name:
                return o
        else:
            return None

    #{ Recovery and migrations

    def resolve_value(self, exc_info, name, raw_or_json_value, source):
        """
        Resolve Raw Value that cannot be deserialized or re-raise exception.

        Default implementation logs an exception and returns default value.

        @param exc_info: Exception info extracted in the handler of either DeserializationError or ValidationError.
        @type exc_info: tuple

        @param name: Name of the option that cannot be deserialized.
        @type name: str

        @param raw_or_json_value: Raw value that cannot be deserialized.
        @type raw_or_json_value: str

        @param source: Source where value originated from.
        @type source: ValueSource

        @return: Value to be used based on Raw Value.
        """
        LOG.error("Unable to deserialize value of \"%s\" from \"%s\":\n%s.", name, raw_or_json_value,
                  traceback.format_exception(*exc_info))
        return self.option_for_name(name)._default

    def migrate(self, version):
        """
        Migrate options in backend from a given version to current one.

        @param version: Version to migrate. Can be None if config does not exist or does not contain value for that option.

        @note: Called even when versions match.
        """
        self.set_value(self.CONFIG_VERSION_OPTION_NAME, self.CONFIG_VERSION)

    def reset(self):
        """
        Reset config be deleting
        @return:
        """
        for o in self.options():
            o.fdel(self)

    def rename_option(self, old_name, new_name, transform=None):
        """
        Rename option by preserving its value and optionally transforming it.

        You should call this method during migration in migrate.

        @param old_name: Old name of the option.
        @type old_name: str

        @param new_name: New name of the option.
        @type new_name: str

        @param transform: Optional callable that accepts current raw value and returns new raw value.
        @type transform: Callable or None
        """

        value = self.get_value(old_name)

        if value is not None:
            self.set_value(new_name, transform(value) if transform else value)

        self.del_value(old_name)

    #{ Cache

    def reset_cache(self):
        """
        Return reset value for the cache.
        """
        return {}

    #{ Backend access

    def get_value(self, name, *, allow_cache=False):
        """
        Extract Raw Value for a given name from the backend.

        @param name: Name of the option to get.
        @type name: str

        @param allow_cache: If True, config will return cached copy if any.
            If value is not known, it will be read from the backend and cached.
        @type allow_cache: bool

        @rtype: str or None
        """
        with self._lock:
            return self.get_value_lock_free(name, allow_cache=allow_cache)

    def set_value(self, name, raw_value, *, allow_cache=False):
        """
        Store Raw Value for a given name in the backend.

        @param name: Name of the option to set.
        @type name: str

        @param allow_cache: If True, value will only be written to the backend if it's different
            than cached copy.
        @type allow_cache: bool

        @param raw_value: Value to set.
        @type raw_value: str
        """
        with self._lock:
            self.set_value_lock_free(name, raw_value, allow_cache=allow_cache)

    def del_value(self, name, *, allow_cache=False):
        """
        Remove value for a given name from the backend.

        @param name: Name of the option to delete.
        @type name: str

        @param allow_cache: If True, value will only be deleted if it exists is known to not exist to cache.
        @type allow_cache: bool
        """
        with self._lock:
            self.del_value_lock_free(name, allow_cache=allow_cache)

    def get_array_value(self, name, *, allow_cache=False):
        """
        Extract an array of Raw Values for a given name from the backend.

        @param name: Name of the array option to get.
        @type name: str

        @param allow_cache: See get_value.
        @type allow_cache: bool

        @rtype: [str] or None
        """
        with self._lock:
            return self.get_array_value_lock_free(name, allow_cache=allow_cache)

    def set_array_value(self, name, value, *, allow_cache=False):
        """
        Store new value which is an array of Raw Values for a given name in the backend.

        @param name: Name of the array option to set.
        @type name: str

        @param value:  Value to set.
        @type value: [str]

        @param allow_cache: See set_value.
        @type allow_cache: bool
        """
        with self._lock:
            self.set_array_value_lock_free(name, value, allow_cache=allow_cache)

    def get_dict_value(self, name, *, allow_cache=False):
        """
        Extract a dict of Raw Values for a given name from the backend.

        @param name: Name of the dict option to get.
        @type name: str

        @param allow_cache: See get_value.
        @type allow_cache: bool

        @rtype: {str: str} or None
        """
        with self._lock:
            return self.get_dict_value_lock_free(name, allow_cache=allow_cache)

    def set_dict_value(self, name, value, *, allow_cache=False):
        """
        Store new value which is a dict of Raw Values for a given name in the backend.

        @param name: Name of the dict option to set.
        @type name: str

        @param value:  Value to set. Must be a dict of serialized values.
        @type value: {str: str}

        @param allow_cache: See set_value.
        @type allow_cache: bool
        """
        with self._lock:
            self.set_dict_value_lock_free(name, value, allow_cache=allow_cache)

    #{ Lock-free backend access

    def get_value_lock_free(self, name, *, allow_cache=False):
        """
        Lock-free version of get_value.

        @see: get_value
        """
        if allow_cache and name in self._cache:
            return self._cache[name]
        else:
            v = self.get_value_cache_free(name)
            self._cache[name] = v
            return v

    def set_value_lock_free(self, name, raw_value, *, allow_cache=False):
        """
        Lock-free version of set_value.

        @see: set_value
        """
        if not allow_cache or name not in self._cache or self._cache[name] != raw_value:
            self.set_value_cache_free(name, raw_value)
            self._cache[name] = raw_value
            LOG.debug("Value of \"%s\" is set to \"%s\".", name, raw_value)

    def del_value_lock_free(self, name, *, allow_cache=False):
        """
        Lock-free version of del_value.

        @see: del_value
        """
        if not allow_cache or name not in self._cache or self._cache[name] is not None:
            self.del_value_cache_free(name)
            self._cache[name] = None
            LOG.debug("Delete value of \"%s\".", name)

    def get_array_value_lock_free(self, name, *, allow_cache=False):
        """
        Lock-free version of get_array_value.

        @see: get_array_value
        """
        if allow_cache and name in self._cache:
            return self._cache[name]
        else:
            v = self.get_array_value_cache_free(name)
            self._cache[name] = v
            return v

    def set_array_value_lock_free(self, name, value, *, allow_cache=False):
        """
        Lock-free version of set_array_value.

        @see: set_array_value
        """
        if not allow_cache or name not in self._cache or self._cache[name] != value:
            self.set_array_value_cache_free(name, value)
            self._cache[name] = value
            LOG.debug("Array value of \"%s\" is set to \"%s\".", name, value)

    def get_dict_value_lock_free(self, name, *, allow_cache=False):
        """
        Lock-free version of get_dict_value.

        @see: get_dict_value
        """
        if allow_cache and name in self._cache:
            return self._cache[name]
        else:
            v = self.get_dict_value_cache_free(name)
            self._cache[name] = v
            return v

    def set_dict_value_lock_free(self, name, value, *, allow_cache=False):
        """
        Lock-free version of set_dict_value.

        @see: set_dict_value
        """
        if not allow_cache or name not in self._cache or self._cache[name] != value:
            self.set_dict_value_cache_free(name, value)
            self._cache[name] = value
            LOG.debug("Dict value of \"%s\" is set to \"%s\".", name, value)

    #{ Cache-free backend access

    @abstractmethod
    def get_value_cache_free(self, name):
        """
        Cache-free version of get_value.

        @see: get_value
        """
        pass

    @abstractmethod
    def set_value_cache_free(self, name, raw_value):
        """
        Cache-free version of set_value.

        @see: set_value
        """
        pass

    @abstractmethod
    def del_value_cache_free(self, name):
        """
        Cache-free version of del_value.

        @see: del_value
        """
        pass

    @abstractmethod
    def get_array_value_cache_free(self, name):
        """
        Cache-free version of get_array_value.

        @see: get_array_value
        """
        pass

    @abstractmethod
    def set_array_value_cache_free(self, name, value):
        """
        Cache-free version of set_array_value.

        @see: set_array_value
        """
        pass

    @abstractmethod
    def get_dict_value_cache_free(self, name):
        """
        Cache-free version of get_dict_value.

        @see: get_dict_value
        """
        pass

    @abstractmethod
    def set_dict_value_cache_free(self, name, value):
        """
        Cache-free version of set_dict_value.

        @see: set_dict_value
        """
        pass

    #}
