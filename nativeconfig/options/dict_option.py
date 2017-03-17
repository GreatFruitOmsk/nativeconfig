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
            raise ValueError("Value option must be instance of one of base options except array and dict!")

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
            raise DeserializationError("Unable to deserialize \"{}\" into dict for \"{}\"!".format(raw_value, self.name), raw_value, self.name)
        else:
            return value

    def serialize_json(self, python_value):
        return '{' + ', '.join(['{}: {}'.format(json.dumps(k), self._value_option.serialize_json(v)) for k, v in python_value.items()]) + '}'

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if isinstance(value, dict):
                return {k: self._value_option.deserialize_json(json.dumps(v)) for k, v in value.items()}
            else:
                raise DeserializationError("\"{}\" is not a JSON dict!".format(json_value), json_value, self.name)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, dict):
            raise ValidationError("Invalid dict \"{}\" for \"{}\"!".format(python_value, self.name), python_value, self.name)

        for v in python_value.values():
            self._value_option.validate(v)
