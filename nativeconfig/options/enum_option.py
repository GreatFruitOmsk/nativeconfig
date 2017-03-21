import enum
import logging

from .base_option import BaseOption, BaseContainerOption
from .float_option import FloatOption
from .int_option import IntOption
from .string_option import StringOption
from nativeconfig.exceptions import DeserializationError, ValidationError


LOG = logging.getLogger('nativeconfig')


class EnumOption(BaseOption):
    """±
    EnumOption represents Python Enum in config.
    """
    def __init__(self, name, enum_type, value_type=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        If value_type is provided, it's used to serialize values. Otherwise Enum names are used.

        @param enum_type: Type that subclasses from enum.Enum that will be used to instantiate python value.
        @type enum_type: enum.EnumMeta

        @param value_type: An instance of BaseOption subclass that provides serialization and validation.
            For known Enum types, value_type will be picked automatically unless set explicitly.
        @type value_type: BaseOption
        """
        if issubclass(enum_type, enum.Enum):
            self._enum_type = enum_type
        else:
            raise ValueError("'enum_type' must be a subclass of enum.Enum")

        if value_type:
            if isinstance(value_type, BaseOption) and not isinstance(value_type, BaseContainerOption):
                self._value_type = value_type
            else:
                raise ValueError("'value_type' cannot be a container option")
        elif issubclass(enum_type, int):
            self._value_type = IntOption('IntOption')
        elif issubclass(enum_type, float):
            self._value_type = FloatOption('FloatOption')
        elif issubclass(enum_type, str):
            self._value_type = StringOption('StringOption')
        else:
            self._value_type = None

        choices = kwargs.pop('choices', tuple(enum_type.__members__.values()))

        super().__init__(name, choices=choices, **kwargs)

    def serialize(self, python_value):
        if self._value_type:
            return self._value_type.serialize(python_value.value)
        else:
            return python_value.name

    def deserialize(self, raw_value):
        """
        1. If value_type is set, will try to instantiate enum by value
        2. Otherwise will try to find an appropriate value by comparing string.
        """
        if self._value_type:
            try:
                return self._enum_type(self._value_type.deserialize(raw_value))
            except (ValueError, DeserializationError):
                pass

        LOG.info("Unable to instantiate \"{}\" directly.", self._enum_type)

        raw_value_lower = raw_value.lower()

        for name, value in self._enum_type.__members__.items():
            if str(value).lower() == raw_value_lower or name.lower() == raw_value_lower:
                return value

        raise DeserializationError("unable to deserialize '{}' into {}".format(raw_value, self._enum_type), raw_value, self.name)

    def serialize_json(self, python_value):
        if self._value_type:
            return self._value_type.serialize_json(python_value.value)
        else:
            return super().serialize_json(python_value.name)

    def deserialize_json(self, json_value):
        if json_value == 'null':
            return None
        elif self._value_type:
            try:
                enum_value = self._value_type.deserialize_json(json_value)
            except DeserializationError:
                enum_value = super().deserialize_json(json_value)
        else:
            enum_value = super().deserialize_json(json_value)

        try:
            return self._enum_type(enum_value)
        except ValueError:
            pass

        try:
            return self._enum_type[enum_value]
        except KeyError:
            pass

        raw_value = str(enum_value)

        return self.deserialize(raw_value)

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, self._enum_type):
            raise ValidationError("'{}' must be in {}".format(python_value, self._enum_type), python_value, self.name)
