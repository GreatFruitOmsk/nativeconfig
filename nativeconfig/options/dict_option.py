import json

from .base_option import BaseOption, BaseContainerOption
from nativeconfig.exceptions import DeserializationError, ValidationError


class DictOption(BaseContainerOption):
    """
    DictOption represents Python dict in config.
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
            raise ValueError("value option must be an instance of BaseOption and not of BaseContainerOption")

        super().__init__(name, getter='get_dict_value', setter='set_dict_value', **kwargs)

    def serialize(self, python_value):
        serializable_dict = {}

        for k, v in python_value.items():
            serialized_v = self._value_option.serialize(v)
            serializable_dict.update({k: serialized_v})

        return serializable_dict

    def deserialize(self, raw_value):
        try:
            deserialized_dict = {}

            for k, v in raw_value.items():
                deserialized_dict.update({k: self._value_option.deserialize(v)})

            value = deserialized_dict
        except DeserializationError:
            raise DeserializationError("unable to deserialize '{}' into dict".format(raw_value), raw_value, self.name)
        else:
            return value

    def serialize_json(self, python_value):
        # A JSON dict of JSON-serialized values must be constructed manually
        # to avoid double-serialization.
        if python_value is not None:
            return '{' + ', '.join(['{}: {}'.format(json.dumps(k), self._value_option.serialize_json(v)) for k, v in python_value.items()]) + '}'
        else:
            return super().serialize_json(python_value)

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if isinstance(value, dict):
                return {k: self._value_option.deserialize_json(json.dumps(v)) for k, v in value.items()}
            else:
                raise DeserializationError("'{}' is not a JSON dict".format(json_value), json_value, self.name)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, dict):
            raise ValidationError("'{}' must be a dict".format(python_value), python_value, self.name)

        for v in python_value.values():
            self._value_option.validate(v)
