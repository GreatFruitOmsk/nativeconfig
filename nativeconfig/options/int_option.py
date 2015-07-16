import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base_option import BaseOption


class IntOption(BaseOption):
    """
    IntOption represents Python int in config.
    """
    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def deserialize(self, raw_value):
        try:
            return int(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize \"{}\" into int for \"{}\"!".format(raw_value, self.name), raw_value, self.name)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid JSON value for \"{}\": \"{}\"!".format(self.name, json_value), json_value, self.name)
        else:
            if value is not None:
                if not isinstance(value, int):
                    raise DeserializationError("\"{}\" is not a JSON integer!".format(json_value), json_value, self.name)
                else:
                    return int(value)
            else:
                return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, int):
            raise ValidationError("Invalid integer \"{}\" for \"{}\"!".format(python_value, self.name), python_value, self.name)
