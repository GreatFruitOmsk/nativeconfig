import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class DictOption(BaseOption):
    """
    DictOption represents Python dict in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return json.dumps(value)

    def deserialize(self, raw_value):
        if type(raw_value) == dict:
            return raw_value
        else:
            try:
                value = json.loads(raw_value)
            except ValueError:
                raise DeserializationError("Unable to deserialize '{}' into dict.".format(raw_value), raw_value)
            else:
                return value

    def validate(self, value):
        super().validate(value)
        try:
            valid_val = dict(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid dict '{}'.".format(value), value)
