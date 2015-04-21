import json
from pathlib import WindowsPath, PosixPath, Path

from nativeconfig.exceptions import ValidationError
from nativeconfig.options.base import BaseOption


class PathOption(BaseOption):
    """
    PathOption represents pathlib's Path in config.

    """

    def __init__(self, name, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)

    def serialize(self, value):
        return str(value)

    def deserialize(self, raw_value):
        return Path(raw_value)

    def serialize_json(self, value):
        return json.dumps(str(value))

    def deserialize_json(self, json_value):
        return Path(json.loads(json_value))

    def validate(self, value):
        super().validate(value)
        if type(value) == PosixPath or type(value) == WindowsPath:
            return
        else:
            raise ValidationError("Invalid path '{}'.".format(value), value)
