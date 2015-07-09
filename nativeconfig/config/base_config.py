from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import inspect
import json
import logging
import threading
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
                if o._name == option._name:
                    if not issubclass(option.__class__, o.__class__):
                        warn("Type (\"{}\") of the \"{}\" option overridden by \"{}\" is different than type (\"{}\") defined by one of super classes.".format(option.__class__.__name__, option._name, base_class.__name__, o.__class__.__name__))
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

    Methods that work with options by name does not fail explicitly but use warnings.warn.

    @cvar CONFIG_VERSION: Version of the config. Used during migrations and usually should be identical to app's __version__.
    @cvar CONFIG_VERSION_OPTION_NAME: Name of the option that represents config version in backend.

    @ivar _ordered_options: Ordered dict of options defined in the order of definition from base class to subclasses.
    """
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
                if attribute_value._name in properties:
                    raise AttributeError("Duplication of option named \"{}\"!".format(attribute_value._name))
                else:
                    properties.add(attribute_value._name)

    def __init__(self):
        self.validate()
        super().__init__()
        self.migrate(self.config_version)

#{ Default options

    config_version = StringOption(CONFIG_VERSION_OPTION_NAME, default=CONFIG_VERSION)

#{ Access options by name

    def get_value_for_option_name(self, name):
        """
        Get option's Raw Value by its name in backend.

        @param name: Name of the option.
        @type name: str

        @return: JSON Value. None if such option does not exist.
        @rtype: str or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            return attribute.serialize_json(attribute.fget(self))
        else:
            warn("No option named \"{}\".".format(name))
            return None

    def set_value_for_option_name(self, name, json_value):
        """
        Set option by its name in backend.

        @param name: Name of the option.
        @type name: str or None

        @param json_value: JSON value. If 'null', value will be deleted.
        @type json_value: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            self.set_value_for_option(attribute, json_value)
        else:
            warn("No option named \"{}\".".format(name))

    def set_one_shot_value_for_option_name(self, name, json_value):
        """
        Set One Shot Value for a given name.

        @param name: Name of the option.
        @type name: str

        @param json_value: JSON value.
        @type json_value: str or dict or list or None
        """
        attribute = self.option_for_name(name)

        if attribute:
            self.set_one_shot_value_for_option(attribute, json_value)
        else:
            warn("No option named \"{}\".".format(name))

    def del_value_for_option_name(self, name):
        """
        Delete option by its name in backend.

        @param name: Name of the option.
        @type name: str
        """
        attribute = self.option_for_name(name)

        if attribute:
            self.del_value_for_option(attribute)
        else:
            warn("No option named \"{}\".".format(name))

    def snapshot(self):
        """
        Get snapshot of current config.

        @return: Ordered JSON dictioary of json-serialized options.
        @rtype: str
        """
        return '{' + ', '.join(['{}: {}'.format(json.dumps(o._name), self.get_value_for_option(o)) for o in self._ordered_options]) + '}'

    def restore_snapshot(self, snapshot):
        """
        Set config values for older snapshot.

        If option represented in snapshot does not exist, warning will be raised.

        @param snapshot: Snapshot as returned by BaseConfig.snapshot
        """
        for k, v in json.loads(snapshot).items():
            # Additional quotes are needed, because values will be loaded into python strings,
            # but set_value_for_option_name expects JSON.
            self.set_value_for_option_name(k, json.dumps(v))

#{ Introspection

    def option_for_name(self, name):
        """
        Return option (property object) for name.

        @param name: Name of an option.
        @type name: str

        @rtype: BaseOption or None
        """
        for option in self._ordered_options:
            if option._name == name:
                return option
        else:
            return None

    def get_value_for_option(self, option):
        """
        Return value of a given option.

        @param option: Option's attribute
        @type option: BaseOption

        @rtype: str
        """
        return option.serialize_json(option.fget(self))

    def set_value_for_option(self, option, json_value):
        """
        Set option value in backend.

        @param option: Option's attribute.
        @type option: BaseOption

        @param json_value: JSON value. If 'null', value will be deleted.
        @type json_value: str
        """
        option.fset(self, option.deserialize_json(json_value))

    def set_one_shot_value_for_option(self, option, json_value):
        """
        Set One Shot Value for a given option.

        @param option: Option's attribute.
        @type option: BaseOption

        @param json_value: JSON value.
        @type json_value: str or dict or list or None
        """
        option.fset(self, option.deserialize_json(json_value))

    def del_value_for_option(self, option):
        """
        Delete option in backend.

        @param option: Option's attribute.
        @type option: BaseOption
        """
        option.fdel(self)

#{ Recovery and migrations

    def resolve_value(self, exception, name, raw_value):
        """
        Resolve Raw Value that cannot be deserialized or re-raise exception.

        Default implementation logs an exception and returns default value.

        @param exception: Exception that was raised during serialization.
        @type exception: DeserializationError or ValidationError

        @param name: Name of the option that cannot be deserialized.
        @type name: str

        @param raw_value: Raw value that cannot be deserialized.
        @type raw_value: str

        @return: Value to be used based on raw value.
        """
        LOG.error("Unable to deserialize value of \"%s\" from \"%s\": %s.", name, raw_value, exception)
        return self.option_for_name(name)._default

    def migrate(self, version):
        """
        Migrate options in backend from a given version to current one.

        @param version: Version to migrate. Can be None if config does not exist or does not contain value for that option.

        @note: Called even when versions match.
        """
        self.set_value(self.CONFIG_VERSION_OPTION_NAME, self.CONFIG_VERSION)

#{ Access backend

    @abstractmethod
    def get_value(self, name):
        """
        Return Raw Value for a given name or None if no value exists and default should be used.

        @param name: Name of the option to get.
        @type name: str

        @rtype: str or None
        """
        pass

    @abstractmethod
    def set_value(self, name, raw_value):
        """
        Set new Raw Value for a given name.

        @param name: Name of the option to set.
        @type name: str

        @param raw_value: Value to set. Must be serialized.
        @type raw_value: str
        """
        pass

    @abstractmethod
    def del_value(self, name):
        """
        Remove value for a given name.

        @param name: Name of the option to delete.
        @type name: str
        """
        pass

    @abstractmethod
    def get_array_value(self, name):
        """
        Return an array of Raw Values for a given name.

        @param name: Name of the array option to get.
        @type name: str

        @rtype: list or None
        """
        pass

    @abstractmethod
    def set_array_value(self, name, value):
        """
        Set new value which is an array of Raw Values for a given name.

        @param name: Name of the array option to set.
        @type name: str

        @param value:  Value to set. Must be a list of serialized values.
        @type value: list
        """
        pass

    @abstractmethod
    def get_dict_value(self, name):
        """
        Return a dict of Raw Values for a given name.

        @param name: Name of the dict option to get.
        @type name: str

        @rtype: dict or None
        """
        pass

    @abstractmethod
    def set_dict_value(self, name, value):
        """
        Set new value which is a dict of Raw Values for a given name.

        @param name: Name of the dict option to set.
        @type name: str

        @param value:  Value to set. Must be a dict of serialized values.
        @type value: dict
        """
        pass
#}
