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
        if type(raw_value) == list:
            return raw_value
        else:
            try:
                value = list(eval(raw_value))
            except (ValueError, TypeError, NameError):
                raise DeserializationError("Unable to deserialize '{}' into array.".format(raw_value), raw_value)
            else:
                return value

    def validate(self, value):
        super().validate(value)
        if type(value) == list:
            return
        else:
            raise ValidationError("Invalid array '{}'.".format(value), value)
