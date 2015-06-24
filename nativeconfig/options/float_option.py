import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base_option import BaseOption


class FloatOption(BaseOption):
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
            value = float(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize \"{}\" into float for \"{}\"!".format(raw_value, self._name), raw_value, self._name)
        else:
            return value

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid json for \"{}\": \"{}\"!".format(self._name, json_value), json_value, self._name)
        else:
            return value

    def validate(self, python_value):
        super().validate(python_value)
        try:
            valid_val = float(python_value)
        except ValueError:
            raise ValidationError("Invalid float \"{}\" for \"{}\"!".format(python_value, self._name), python_value, self._name)
