from abc import ABC
import json
import logging
import os

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError


LOG = logging.getLogger('nativeconfig')


class BaseOption(property, ABC):
    """
    Base class for all options.

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

        @raise InitializationError: If any of arguments is incorrect. Only handles most obvious errors.
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
            raise InitializationError("'name' cannot be empty.")

        if env_name is not None and len(env_name) == 0:
            raise InitializationError("'env_name' cannot be empty.")

        if choices is not None and len(choices) == 0:
            raise InitializationError("'choices' cannot be empty.")

        if choices is not None:
            for c in choices:
                self.validate(c)

        if default is not None:
            self.validate(default)

    def set_one_shot_value(self, value):
        """
        Set one shot value of the option that overrides value from storage but can be reset by set.

        Useful if you want to allow a user to override the option via CLI.

        @raise ValidationError: Raise if value is not valid.
        """
        self.validate(value)
        self._one_shot_value = None

#{ Validation

    def validate(self, value):
        """
        Validate value. Must raise ValidationError if value is wrong.

        @raise ValidationError: Raise if value is wrong.
        """
        if value is None:
            return

        if self._choices is not None and value not in self._choices:
            raise ValidationError("Value '{}' is not one of the choices {}.".format(value, self._choices), value)

#{ Serialization and deserialization

    def serialize(self, value):
        """
        Serialize value into raw value.

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
        Serialize value into json compatible string.

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

#{ Access backend

    def fget(self, enclosing_self):
        """
        @raise DeserializationError: Raise if value cannot be deserialized or deserialized value isn't one of choices.
        """
        raw_v = None

        if self._env_name:
            raw_v = os.getenv(self._env_name)
            if raw_v is not None:
                LOG.debug("value of '%s' is overridden by environment variable: %s", self._name, raw_v)
                raw_v = self.deserialize_json(raw_v)

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
                self.validate(value)
                return value
            except (DeserializationError, ValidationError) as e:
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
#}
