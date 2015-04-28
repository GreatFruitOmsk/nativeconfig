import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base_option import BaseOption


class StringOption(BaseOption):
    """
    StringOption represents Python string in config.
    """
    def __init__(self, name, *, allow_empty=True, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        @param allow_empty: Allow values of empty string.
        @type allow_empty: bool
        """
        self._allow_empty = allow_empty
        super().__init__(name, **kwargs)

    def serialize(self, python_value):
        return str(python_value)

    def deserialize(self, raw_value):
        return str(raw_value)  # return a copy

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid json: \"{}\"".format(json_value), json_value)
        else:
            return value

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, str):
            raise ValidationError("Invalid string value \"{}\"!".format(python_value), python_value)

        if not self._allow_empty and len(python_value) == 0:
            raise ValidationError("Empty values are disallowed!", python_value)
