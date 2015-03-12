import json
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class PathOption(BaseOption):
    """
    FloatOption represents Python float in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw_value):
        try:
            value = PurePath(raw_value)
        except ValueError:
            raise DeserializationError("Unable to deserialize '{}' into path.".format(raw_value), raw_value)
        else:
            return value

    def serialize_json(self, value):
        return json.dumps(str(value))

    def deserialize_json(self, json_value):
        return PurePath(json.loads(json_value))

    def validate(self, value):
        super().validate(value)
        if type(value) == PurePosixPath or type(value) == PureWindowsPath:
            return
        else:
            raise ValidationError("Invalid path '{}'.".format(value), value)
