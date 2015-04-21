import json
from nativeconfig.exceptions import DeserializationError, ValidationError, InitializationError
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
        if value_option:
            from nativeconfig.options import ArrayOption

            if isinstance(value_option, BaseOption) \
            and not isinstance(value_option, ArrayOption) \
            and not isinstance(value_option, DictOption):
                self._value_option = value_option
            else:
                raise InitializationError("Value option must be instance of one of base options except array and dict")
        else:
            self._value_option = None

    def serialize(self, value):
        serializable_dict = {}
        if isinstance(self._value_option, BaseOption):
            for k, v in value.items():
                serialized_v = self._value_option.serialize(v)
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
                if isinstance(self._value_option, BaseOption):
                    deserialized_dict = {}
                    for k, v in raw_dict.items():
                        deserialized_dict.update({k: self._value_option.deserialize(v)})
                    value = deserialized_dict
                else:
                    value = raw_dict
            except ValueError:
                raise DeserializationError("Unable to deserialize '{}' into dict.".format(raw_value), raw_value)
            else:
                return value

    def serialize_json(self, value):
        serializable_dict = {}
        if isinstance(self._value_option, BaseOption):
            for k, v in value.items():
                serialized_v = self._value_option.serialize(v)
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
