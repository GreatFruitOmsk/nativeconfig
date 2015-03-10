from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class StringOption(BaseOption):
    """
    FloatOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices and default_if_empty.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value).encode('utf-8')

    def deserialize(self, raw_value):
        if raw_value == "":
            raise DeserializationError("unable to deserialize value '{}'".format(raw_value), raw_value)
        else:
            try:
                value = eval(raw_value).decode('utf-8')
            except (ValueError, TypeError):
                raise DeserializationError("unable to deserialize value '{}'".format(raw_value), raw_value)
            else:
                return value

    def validate(self, value):
        super().validate(value)
        if type(value) == str:
            return
        else:
            raise ValidationError("Unable to validate '{}'".format(value), value)
