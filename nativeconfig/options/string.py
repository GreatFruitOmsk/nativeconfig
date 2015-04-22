from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class StringOption(BaseOption):
    """
    StringOption represents Python string in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, python_value):
        return str(python_value).encode('utf-8')

    def deserialize(self, raw_value):
        if raw_value == "":
            raise DeserializationError("Unable to deserialize \"{}\" into string value!".format(raw_value), raw_value)
        else:
            try:
                value = eval(raw_value).decode('utf-8')
            except (ValueError, TypeError):
                raise DeserializationError("Unable to deserialize \"{}\" into string value!".format(raw_value), raw_value)
            else:
                return value

    def validate(self, python_value):
        super().validate(python_value)
        if type(python_value) == str:
            return
        else:
            raise ValidationError("Invalid string value \"{}\"!".format(python_value), python_value)
