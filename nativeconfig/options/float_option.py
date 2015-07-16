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

    def deserialize(self, raw_value):
        try:
            value = float(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize \"{}\" into float for \"{}\"!".format(raw_value, self.name), raw_value, self.name)
        else:
            return value

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid JSON value for \"{}\": \"{}\"!".format(self.name, json_value), json_value, self.name)
        else:
            if value is not None:
                if not isinstance(value, float):
                    raise DeserializationError("\"{}\" is not a JSON float!".format(json_value), json_value, self.name)
                else:
                    return float(value)
            else:
                return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, float):
            raise ValidationError("Invalid float \"{}\" for \"{}\"!".format(python_value, self.name), python_value, self.name)
