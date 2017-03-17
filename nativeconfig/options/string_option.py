from .base_option import BaseOption
from nativeconfig.exceptions import DeserializationError, ValidationError


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

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, str):
                raise DeserializationError("'{}' is not a JSON string".format(json_value), json_value, self.name)
            else:
                return str(value)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, str):
            raise ValidationError("'{}' must be an str".format(python_value), python_value, self.name)

        if not self._allow_empty and len(python_value) == 0:
            raise ValidationError("empty values are invalid", python_value, self.name)
