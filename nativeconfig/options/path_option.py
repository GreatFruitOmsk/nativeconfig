from pathlib import PurePath, Path

from .base_option import BaseOption
from nativeconfig.exceptions import ValidationError, DeserializationError


class PathOption(BaseOption):
    """
    PathOption represents pathlib's Path in config.
    """

    def __init__(self, name, *, path_type=Path, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        @type path_type: PurePath
        """
        if not issubclass(path_type, PurePath):
            raise ValueError("'path_type' must be a subclass of PurePath")

        self._path_type = path_type

        # call superclass's init() after _path_type initialization because BaseOption's init() calls validate(),
        # and in validate() we must already have valid _path_type
        super().__init__(name, **kwargs)

    def deserialize(self, raw_value):
        return self._path_type(raw_value)

    def serialize_json(self, python_value):
        return super().serialize_json(str(python_value) if python_value is not None else None)

    def deserialize_json(self, json_value):
        value = super().deserialize_json(json_value)

        if value is not None:
            if not isinstance(value, str):
                raise DeserializationError("'{}' is not a JSON string".format(json_value), json_value, self.name)
            else:
                return self._path_type(value)
        else:
            return None

    def validate(self, python_value):
        super().validate(python_value)

        if not isinstance(python_value, self._path_type):
            raise ValidationError("'{}' must be a {}".format(python_value, self._path_type), python_value, self.name)
