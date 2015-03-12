from nativeconfig.exceptions import DeserializationError
from nativeconfig.options.base import BaseOption


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
        Accepts all the arguments of BaseConfig except choices and default_if_empty.
        """
        super().__init__(name, choices=[True, False], **kwargs)

    def serialize(self, value):
        return '1' if value else '0'

    def deserialize(self, raw_value):
        if raw_value.upper() in self.TRUE_RAW_VALUES:
            return True
        elif raw_value.upper() in self.FALSE_RAW_VALUES:
            return False
        else:
            raise DeserializationError("Value '{}' must be one of {}.".format(raw_value, self.ALLOWED_RAW_VALUES), raw_value)
