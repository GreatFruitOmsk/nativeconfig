from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class IntOption(BaseOption):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw_value):
        try:
            return int(raw_value)
        except ValueError:
            raise DeserializationError("Unable to  deserialize \"{}\" as valid int value".format(raw_value), raw_value)

    def validate(self, value):
        super().validate(value)
        try:
            valid_val = int(value)
        except ValueError as e:
            raise ValidationError("Unable to validate \"{}\"".format(value), value)
