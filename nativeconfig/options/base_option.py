from abc import ABCMeta
import copy
from enum import Enum
import json
import logging
import os
import sys

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError


LOG = logging.getLogger('nativeconfig')


class ValueSource(Enum):
    resolver = 1
    default = 2
    config = 3
    one_shot = 4
    env = 5


class BaseOption(property, metaclass=ABCMeta):
    """
    Base class for all options.

    Value of each option can be represented by three different versions:

        1. Python Value: used in the code
        2. Raw Value (utf-8 sting): used to store in underlying config
        3. JSON Value: used to interact with the user

    Value of an option can be overridden by an environment variable.

    Setting option to None is equivalent to deleting it.

    @raise Error: Raise if any of the arguments has inappropriate value.
    @raise ValidationError: Raise if default value or any of the choices values is invalid.
    """
    def __init__(self,
                 name,
                 *,
                 getter='get_value',
                 setter='set_value',
                 deleter='del_value',
                 resolver='resolve_value',
                 choices=None,
                 env_name=None,
                 default=None,
                 allow_cache=None,
                 doc=None):
        """
        @param name: Name of the property.
        @type name: str

        @param getter: Name of the method of the enclosing class to get value.

        @param setter: Name of the of the enclosing class to set value.

        @param deleter: Name of the deleter of the enclosing class to delete value.

        @param resolver: Name of the resolver of the enclosing class to resolve value that cannot be serialized.

        @param choices: List of allowed Python Values for the option. Deep copied.

        @param env_name: Name of the env variable that contains JSON Value that can override value of the option.
        @type env_name: str

        @param default: Default Python Value of the option. Deep copied.

        @param allow_cache: Whether value can be cached.
        @type allow_cache: bool

        @raise InitializationError: If any of arguments is incorrect. Only handles most obvious errors.
        @raise ValidationError: If default or any of choices is invalid.
        """
        super(BaseOption, self).__init__(self.fget, self.fset, self.fdel, doc=doc or self.__doc__)

        self._name = name
        self._getter = getter
        self._setter = setter
        self._deleter = deleter
        self._resolver = resolver
        self._choices = copy.deepcopy(choices) if choices is not None else choices
        self._env_name = env_name
        self._default = copy.deepcopy(default) if default is not None else default
        self._allow_cache = allow_cache
        self.__doc__ = doc or self.__doc__

        self._one_shot_value = None
        self._is_one_shot_value_set = False  # None is allowed for One Shot Value

        if not name:
            raise InitializationError("\"name\" cannot be empty!")

        if env_name is not None and len(env_name) == 0:
            raise InitializationError("\"env_name\" cannot be empty!")

        if choices is not None and len(choices) == 0:
            raise InitializationError("\"choices\" cannot be empty!")

        if choices is not None:
            for c in choices:
                self.validate(c)

        if default is not None:
            self.validate(default)

    @property
    def name(self):
        return self._name

    @property
    def choices(self):
        return copy.deepcopy(self._choices)

    @property
    def default(self):
        return copy.deepcopy(self._default)

    def set_one_shot_value(self, python_value):
        """
        Set One Shot Value of the option that overrides Raw Value from storage but can be reset by set.

        Useful if you want to allow a user to temporary override the option via CLI.

        @raise ValidationError: Raise if python_value is not valid.
        """
        if python_value is not None:
            self.validate(python_value)
        self._one_shot_value = python_value
        self._is_one_shot_value_set = True

#{ Validation

    def validate(self, python_value):
        """
        Validate Python Value. Must raise ValidationError if value is wrong.

        @raise ValidationError: Raise if value is wrong.
        """
        if python_value is None:
            return

        if self._choices is not None and python_value not in self._choices:
            raise ValidationError("Value \"{}\" is not one of the choices {} allowed for \"{}\"!".format(python_value, self._choices, self.name), python_value, self.name)

#{ Serialization and deserialization

    def serialize(self, python_value):
        """
        Serialize Python Value into Raw Value.

        @see: deserialize

        @raise SerializationError: Raise if value cannot be serialized.
        """
        return str(python_value)

    def deserialize(self, raw_value):
        """
        Deserialize Raw Value into Python Value.

        @see: serialize

        @raise DeserializationError: Raise if value cannot be deserialized.
        """
        return str(raw_value)

    def serialize_json(self, python_value):
        """
        Serialize Python Value into JSON Value.

        @see: deserialize_json

        @rtype: str
        """
        return json.dumps(python_value)

    def deserialize_json(self, json_value):
        """
        Deserialize JSON Value into Python Value.

        @see: serialize_json
        """
        return json.loads(json_value)

#{ Access backend

    def read_value(self, enclosing_self):
        """
        Read value for the option from all supported sources.

        @param enclosing_self: Instance of class that defines this property.

        @rtype: (object, ValueSource)
        """
        def make_python_value_from_json_value(json_value, source):
            try:
                python_value = self.deserialize_json(json_value)
                self.validate(python_value)
                return python_value, source
            except (DeserializationError, ValidationError):
                return getattr(enclosing_self, self._resolver)(sys.exc_info(), self.name, json_value, source), ValueSource.resolver

        def make_python_value_from_raw_value(raw_value, source):
            try:
                python_value = self.deserialize(raw_value)
                self.validate(python_value)
                return python_value, source
            except (DeserializationError, ValidationError):
                return getattr(enclosing_self, self._resolver)(sys.exc_info(), self.name, raw_value, source), ValueSource.resolver

        python_value, source = None, None

        if self._env_name:
            json_value = os.getenv(self._env_name)
            if json_value is not None:
                LOG.debug("value of \"%s\" is overridden by environment variable: %s.", self.name, json_value)
                python_value, source = make_python_value_from_json_value(json_value, ValueSource.env)

        if python_value is None and self._is_one_shot_value_set:
            LOG.debug("value of \"%s\" is temporary overridden by one shot value: %s.", self.name, self._one_shot_value)
            python_value, source = self._one_shot_value, ValueSource.one_shot
        elif python_value is None:
            allow_cache = self._allow_cache or (hasattr(enclosing_self, 'ALLOW_CACHE') and enclosing_self.ALLOW_CACHE)
            raw_value = getattr(enclosing_self, self._getter)(self.name, allow_cache=allow_cache)
            if raw_value is not None:
                python_value, source = make_python_value_from_raw_value(raw_value, ValueSource.config)

        if python_value is None:
            LOG.debug("No value is set for \"%s\", use default.", self.name)
            python_value, source = self._default, ValueSource.default

        return python_value, source

    def fget(self, enclosing_self):
        """
        Read Raw Value from the storage and deserialized it into Python Value.

        If either DeserializationError or ValidationError occurs in process, they will be forwarded to resolver.

        @param enclosing_self: Instance of class that defines this property.
        """
        return self.read_value(enclosing_self)[0]

    def fset(self, enclosing_self, python_value):
        """
        Serialize Python Value into Raw Value and write it to storage.

        Resets One Shot Value.
        Setting None simply deletes Raw Value from storage.

        @param enclosing_self: Instance of class that defines this property.

        @param python_value: Python Value to be set.
        """
        self._one_shot_value = None
        self._is_one_shot_value_set = False

        if python_value is not None:
            self.validate(python_value)
            raw_value = self.serialize(python_value)
            allow_cache = self._allow_cache or (hasattr(enclosing_self, 'ALLOW_CACHE') and enclosing_self.ALLOW_CACHE)
            getattr(enclosing_self, self._setter)(self.name, raw_value, allow_cache=allow_cache)
        else:
            self.fdel(enclosing_self)

    def fdel(self, enclosing_self):
        """
        Delete Raw Value from the config.

        @param enclosing_self: Instance of class that defines this property.
        """
        self._one_shot_value = None
        self._is_one_shot_value_set = False
        allow_cache = self._allow_cache or (hasattr(enclosing_self, 'ALLOW_CACHE') and enclosing_self.ALLOW_CACHE)
        getattr(enclosing_self, self._deleter)(self.name, allow_cache=allow_cache)
#}
