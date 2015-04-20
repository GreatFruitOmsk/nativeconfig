from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


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
            raise DeserializationError("Unable to deserialize '{}' into float value.".format(raw_value), raw_value)
        else:
            return value

    def validate(self, python_value):
        super().validate(python_value)
        try:
            valid_val = float(python_value)
        except ValueError:
            raise ValidationError("Invalid float value '{}'.".format(python_value), python_value)
