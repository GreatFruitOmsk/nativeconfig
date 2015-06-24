import json
from pathlib import PurePath, Path

from nativeconfig.exceptions import ValidationError, InitializationError, DeserializationError
from nativeconfig.options.base_option import BaseOption


class PathOption(BaseOption):
    """
    PathOption represents pathlib's Path in config.
    """

    def __init__(self, name, *, path_type=Path, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        try:
            if not issubclass(path_type, PurePath):
                raise InitializationError(
                    "Path type should be subclass of PurePath")
        except:
            raise InitializationError(
                "Path type should be subclass of PurePath")

        self._path_type = path_type

        # call superclass's init() after _path_type initialization because BaseOption's init() calls validate(),
        # and in validate() we must already have valid _path_type
        super().__init__(name, **kwargs)

    def serialize(self, python_value):
        return str(python_value)

    def deserialize(self, raw_value):
        return self._path_type(raw_value)

    def serialize_json(self, python_value):
        return json.dumps(str(python_value))

    def deserialize_json(self, json_value):
        try:
            raw_path = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid json for \"{}\": \"{}\"!".format(self._name, json_value), json_value, self._name)
        else:
            return self._path_type(raw_path)

    def validate(self, python_value):
        super().validate(python_value)
        if not isinstance(python_value, self._path_type):
            raise ValidationError("Invalid path \"{}\" for \"{}\"!".format(python_value, self._name), python_value, self._name)
