from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class FloatOption(BaseOption):
    """
    FloatOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices and default_if_empty.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw_value):
        try:
            value = float(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize '{}' into float value.".format(raw_value), raw_value)
        else:
            return value

    def validate(self, value):
        super().validate(value)
        try:
            valid_val = float(value)
        except ValueError:
            raise ValidationError("Invalid float value '{}'.".format(value), value)
