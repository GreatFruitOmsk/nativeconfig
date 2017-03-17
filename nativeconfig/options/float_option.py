from .base_option import BaseOption
from nativeconfig.exceptions import DeserializationError, ValidationError


class FloatOption(BaseOption):
    """
    FloatOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def deserialize(self, raw_value):
        try:
            value = float(raw_value)
        except ValueError:
            raise DeserializationError("unable to deserialize '{}' into float".format(raw_value), raw_value, self.name)
        else:
            return value

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, float):
                raise DeserializationError("'{}' is not a JSON float".format(json_value), json_value, self.name)
            else:
                return float(value)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, float):
            raise ValidationError("'{}' must be a float".format(python_value), python_value, self.name)
