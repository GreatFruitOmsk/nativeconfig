import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class DictOption(BaseOption):
    """
    DictOption represents Python dict in config. DictOption can contain other Options as values of dict.

    """

    def __init__(self, name, value_option=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)
        self.value_option = value_option

    def serialize(self, value):
        serializable_dict = {}
        if isinstance(self.value_option, BaseOption):
            for k, v in value.items():
                serialized_v = self.value_option.serialize(v)
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
                if isinstance(self.value_option, BaseOption):
                    deserialized_dict = {}
                    for k, v in raw_dict.items():
                        deserialized_dict.update({k: self.value_option.deserialize(v)})
                    value = deserialized_dict
                else:
                    value = raw_dict
            except ValueError:
                raise DeserializationError("Unable to deserialize '{}' into dict.".format(raw_value), raw_value)
            else:
                return value

    def serialize_json(self, value):
        serializable_dict = {}
        if isinstance(self.value_option, BaseOption):
            for k, v in value.items():
                serialized_v = self.value_option.serialize(v)
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
