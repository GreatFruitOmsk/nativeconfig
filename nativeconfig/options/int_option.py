import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base_option import BaseOption


class IntOption(BaseOption):
    """
    FloatOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, python_value):
        return str(python_value)

    def deserialize(self, raw_value):
        try:
            return int(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize \"{}\" into int value!".format(raw_value), raw_value)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid json: \"{}\"".format(json_value), json_value)
        else:
            return value

    def validate(self, python_value):
        super().validate(python_value)
        try:
            valid_val = int(python_value)
        except ValueError as e:
            raise ValidationError("Invalid value \"{}\" for \"{}\"!".format(python_value, self._name), python_value, self._name)
