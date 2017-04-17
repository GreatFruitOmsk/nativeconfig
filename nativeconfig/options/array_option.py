import json

from .base_option import BaseOption, BaseContainerOption
from nativeconfig.exceptions import DeserializationError, ValidationError


class ArrayOption(BaseContainerOption):
    """
    ArrayOption represents Python arrays in config. ArrayOption can contain other Options as elements
    """
    def __init__(self, name, value_option, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        @param value_option: An instance of BaseOption subclass that provides serialization
            and validation.
        @type value_option: BaseOption
        """
        if isinstance(value_option, BaseOption) and not isinstance(value_option, BaseContainerOption):
            self._value_option = value_option
        else:
            raise ValueError("value option must be a BaseOption but not BaseContainerOption")

        super().__init__(name, setter='set_array_value', getter='get_array_value', **kwargs)

    def serialize(self, python_value):
        serializable_list = []

        for i in python_value:
            serializable_list.append(self._value_option.serialize(i))

        return serializable_list

    def deserialize(self, raw_value):
        try:
            deserialized_list = []

            for i in raw_value:
                deserialized_list.append(self._value_option.deserialize(i))

            value = deserialized_list
        except DeserializationError:
            raise DeserializationError("unable to deserialize '{}' into array".format(raw_value), raw_value, self.name)
        else:
            return value

    def serialize_json(self, python_value):
        # A JSON array of JSON-serialized values must be constructed manually
        # to avoid double-serialization.
        if python_value is not None:
            return '[' + ', '.join([self._value_option.serialize_json(v) for v in python_value]) + ']'
        else:
            return super().serialize_json(python_value)

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, list):
                raise DeserializationError("'{}' is not a JSON array".format(json_value), json_value, self.name)
            else:
                return [self._value_option.deserialize_json(json.dumps(v)) for v in value]
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, (list, tuple)):
            raise ValidationError("'{}' must be a list or tuple".format(python_value), python_value, self.name)

        for v in python_value:
            self._value_option.validate(v)
