import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class ArrayOption(BaseOption):
    """
    ArrayOption represents Python float in config.

    """

    def __init__(self, name, container_type=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)
        self._container_type = container_type

    def serialize(self, value):
        serializable_list = []
        if isinstance(self._container_type, BaseOption):
            for i in value:
                serializable_list.append(self._container_type.serialize(i))
            return str(serializable_list)
        else:
            return str(value)

    def deserialize(self, raw_value):
        if type(raw_value) == list:
            return raw_value
        else:
            try:
                raw_list = list(eval(raw_value))
                if isinstance(self._container_type, BaseOption):
                    deserizlized_list = []
                    for i in raw_list:
                        deserizlized_list.append(self._container_type.deserialize(i))
                    value = deserizlized_list
                else:
                    value = raw_list
            except (ValueError, TypeError, NameError):
                raise DeserializationError("Unable to deserialize '{}' into array.".format(raw_value), raw_value)
            else:
                return value

    def serialize_json(self, value):
        serializable_list = []
        if isinstance(self._container_type, BaseOption):
            for i in value:
                serializable_list.append(self._container_type.serialize(i))
            return json.dumps(serializable_list)
        else:
            return json.dumps(value)

    def validate(self, value):
        super().validate(value)
        if type(value) == list:
            return
        else:
            raise ValidationError("Invalid array '{}'.".format(value), value)
