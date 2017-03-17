from .base_option import BaseOption
from nativeconfig.exceptions import DeserializationError, ValidationError


class BooleanOption(BaseOption):
    """
    BooleanOption represents Python bool (True or False) in config.

    It's smart and is able to properly decode variety of raw values into Python bool.

    @cvar TRUE_VALUES: Tuple of allowed raw values that can be decoded into bool.
    @cvar FALSE_VALUES: Tuple of allowed raw values that can be decoded into bool.
    @cvar ALLOWED_VALUES: Tuple of all allowed raw values.
    """
    TRUE_RAW_VALUES = ('1', 'YES', 'TRUE', 'ON')
    FALSE_RAW_VALUES = ('0', 'NO', 'FALSE', 'OFF')
    ALLOWED_RAW_VALUES = TRUE_RAW_VALUES + FALSE_RAW_VALUES

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        choices = kwargs.pop('choices', (True, False))
        super().__init__(name, choices=choices, **kwargs)

    def serialize(self, python_value):
        return '1' if python_value else '0'

    def deserialize(self, raw_value):
        if raw_value.upper() in self.TRUE_RAW_VALUES:
            return True
        elif raw_value.upper() in self.FALSE_RAW_VALUES:
            return False
        else:
            raise DeserializationError("'{}' must be in {}".format(raw_value, self.ALLOWED_RAW_VALUES), raw_value, self.name)

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, bool):
                raise DeserializationError("'{}' is not a JSON boolean".format(json_value), json_value, self.name)
            else:
                return bool(value)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, bool):
            raise ValidationError("'{}' must be a bool".format(python_value), python_value, self.name)
