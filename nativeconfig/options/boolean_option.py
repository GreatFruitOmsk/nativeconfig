import json
from nativeconfig.exceptions import DeserializationError
from nativeconfig.options.base_option import BaseOption


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
        super().__init__(name, choices=[True, False], **kwargs)

    def serialize(self, python_value):
        return '1' if python_value else '0'

    def deserialize(self, raw_value):
        if raw_value.upper() in self.TRUE_RAW_VALUES:
            return True
        elif raw_value.upper() in self.FALSE_RAW_VALUES:
            return False
        else:
            raise DeserializationError("Value \"{}\" must be one of {} for \"{}\"!".format(raw_value, self.ALLOWED_RAW_VALUES, self.name), raw_value, self.name)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid JSON value for \"{}\": \"{}\"!".format(self.name, json_value), json_value, self.name)
        else:
            if value is not None:
                if not isinstance(value, bool):
                    raise DeserializationError("\"{}\" is not a JSON boolean!".format(json_value), json_value, self.name)
                else:
                    return bool(value)
            else:
                return None
