from array import array
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class ArrayOption(BaseOption):
    """
    ArrayOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw_value):
        if type(raw_value) == array:
            return value
        else:
            try:
                value = array(raw_value)
            except ValueError:
                raise DeserializationError("Unable to deserialize '{}' into float value.".format(raw_value), raw_value)
            else:
                return value

    def validate(self, value):
        super().validate(value)
        try:
            valid_val = array(value)
        except ValueError:
            raise ValidationError("Invalid float value '{}'.".format(value), value)
