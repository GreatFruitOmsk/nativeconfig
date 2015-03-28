from abc import ABCMeta, abstractmethod
import logging
import threading

from nativeconfig.options.base import BaseOption


LOG = logging.getLogger('nativeconfig')


class BaseConfig(metaclass=ABCMeta):
    """
    Base class for all configs.

    Users are supposed to subclass for each config backend and then instantiate singleton via the get_instance method.

    @cvar CONFIG_VERSION: Version of the config. Used during migrations and usually should be identical to app's __version__.
    @cvar CONFIG_VERSION_OPTION_NAME: Name of the option that represents config version in backend.
    """
    CONFIG_VERSION = None
    CONFIG_VERSION_OPTION_NAME = "ConfigVersion"

    _instances = {}
    _instances_events = {}
    _instances_lock = threading.Lock()

    def __init__(self):
        self.validate()
        super().__init__()
        self.migrate(self.get_value(self.CONFIG_VERSION))

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

        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)

            if isinstance(attribute, BaseOption):
                if attribute._name in properties:
                    raise AttributeError("Duplication of property named {}!".format(attribute._name))
                else:
                    properties.add(attribute._name)

#{ Access options by name

    def get_value_for_option_name(self, name):
        """
        Get option's raw value by its name in backend.

        @param name: Name of the option.
        @type name: str

        @return: JSON-encoded raw value. None if such option does not exist.
        @rtype: str or dict or list or None
        """
        attribute = self.property_for_option_name(name)

        if attribute:
            return attribute.serialize_json(attribute.fget(self))
        else:
            LOG.warning("No option named '%s'.", name)

    def set_value_for_option_name(self, name, value):
        """
        Set option by its name in backend.

        @param name: Name of the option.
        @type name: str

        @param value: JSON-encoded raw value.
        @type value: str
        """
        attribute = self.property_for_option_name(name)

        if attribute:
            attribute.fset(self, attribute.deserialize_json(value))
        else:
            LOG.warning("No option named '%s'.", name)

    def set_one_shot_value_for_option_name(self, name, value):
        attribute = self.property_for_option_name(name)

        if attribute:
            attribute.fset(self, attribute.deserialize_json(value))
        else:
            LOG.warning("No option named '%s'.", name)

    def del_value_for_option_name(self, name):
        """
        Delete option by its name in backend.

        @param name: Name of the option.
        @type name: str
        """
        attribute = self.property_for_option_name(name)

        if attribute:
            attribute.fdel(self)
        else:
            LOG.warning("No option named '%s'.", name)

    def snapshot(self):
        """
        Get snapshot of current config.

        @return: Dict of option: value format.
        @rtype: dict
        """
        options = {}

        for attribute_name in dir(type(self)):
            attribute = getattr(type(self), attribute_name)

            if isinstance(attribute, BaseOption):
                name = attribute._name
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

#{ Recovery and migrations

    @abstractmethod
    def resolve_value(self, exception, name, raw_value):
        """
        Resolve raw value that cannot be deserialized or re-raise exception.

        Logs error message and returns default.

        Default implementation logs an exception and returns default value.

        @param exception: Exception that was raised during serialization.
        @type exception: DeserializationError

        @param name: Name of the option that cannot be deserialized.
        @type name: str

        @param raw_value: Raw value that cannot be deserialized.
        @type raw_value: str

        @return: Value to be used based on raw value.
        """
        LOG.error("Unable to deserialize value of '%s' from '%s': %s.", name, raw_value, exception)
        return self.property_for_option_name(name)._default

    @abstractmethod
    def migrate(self, version):
        self.set_value(self.CONFIG_VERSION_OPTION_NAME, version)

#{ Access backend

    @abstractmethod
    def get_value(self, name):
        """
        Return raw value for a given name or None if no value exists and default should be used.

        @param name: Name of the option to get.
        @type name: str

        @rtype: str or None
        """
        pass

    @abstractmethod
    def set_value(self, name, raw_value):
        """
        Set new value for a given name.

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
        Return an array of raw values for a given name.

        @param name: Name of the array option to get.
        @type name: str

        @rtype: list or None
        """
        pass

    @abstractmethod
    def set_array_value(self, name, value):
        """
        Set new value for a given name.

        @param name: Name of the array option to set.
        @type name: str

        @param value:  Value to set. Must be a list of serialized values.
        @type value: list
        """
        pass

    @abstractmethod
    def get_dict_value(self, name):
        """
        Return a dict of raw values for a given name.

        @param name: Name of the dict option to get.
        @type name: str

        @rtype: dict or None
        """
        pass

    @abstractmethod
    def set_dict_value(self, name, value):
        """
        Set new value for a given name.

        @param name: Name of the dict option to set.
        @type name: str

        @param value:  Value to set. Must be a dict of serialized values.
        @type value: dict
        """
        pass
#}
