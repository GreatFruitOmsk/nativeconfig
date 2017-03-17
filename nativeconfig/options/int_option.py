from .base_option import BaseOption
from nativeconfig.exceptions import DeserializationError, ValidationError


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
            raise DeserializationError("unable to deserialize '{}' into int".format(raw_value), raw_value, self.name)

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, int):
                raise DeserializationError("'{}' is not a JSON integer".format(json_value), json_value, self.name)
            else:
                return int(value)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, int):
            raise ValidationError("'{}' must be an int".format(python_value), python_value, self.name)
