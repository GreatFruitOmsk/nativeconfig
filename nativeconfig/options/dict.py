import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class DictOption(BaseOption):
    """
    DictOption represents Python dict in config.

    """

    def __init__(self, name, container_type=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)
        self._container_type = container_type

    def serialize(self, value):
        serializable_dict = {}
        if isinstance(self._container_type, BaseOption):
            for k, v in value.items():
                serialized_v = self._container_type.serialize(v)
                serializable_dict.update({k: serialized_v})
            return json.dumps(serializable_dict)
        else:
            return json.dumps(value)

    def deserialize(self, raw_value):
        if type(raw_value) == dict:
            return raw_value
        else:
            try:
                raw_dict = json.loads(raw_value)
                if self._container_type is not None:
                    deserialized_dict = {}
                    for k, v in raw_dict.items():
                        deserialized_dict.update({k: self._container_type.deserialize(v)})
                    value = deserialized_dict
                else:
                    value = raw_dict
            except ValueError:
                raise DeserializationError("Unable to deserialize '{}' into dict.".format(raw_value), raw_value)
            else:
                return value

    def serialize_json(self, value):
        serializable_dict = {}
        if self._container_type is not None:
            for k, v in value.items():
                serialized_v = self._container_type.serialize(v)
                serializable_dict.update({k: serialized_v})
            return json.dumps(serializable_dict)
        else:
            return json.dumps(value)

    def validate(self, value):
        super().validate(value)
        try:
            valid_val = dict(value)
        except (ValueError, TypeError):
            raise ValidationError("Invalid dict '{}'.".format(value), value)
