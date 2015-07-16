import json
from nativeconfig.exceptions import DeserializationError, ValidationError, InitializationError
from nativeconfig.options.base_option import BaseOption


class DictOption(BaseOption):
    """
    DictOption represents Python dict in config. DictOption can contain other Options as values of dict.
    """
    def __init__(self, name, value_option=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        @param value_option: An instance of BaseOption subclass that provides serialization
                             and validation.
        @type value_option: BaseOption
        """
        super().__init__(name, getter='get_dict_value', setter='set_dict_value', **kwargs)
        if value_option:
            from nativeconfig.options import ArrayOption

            if isinstance(value_option, BaseOption) and not isinstance(value_option, ArrayOption) and not isinstance(value_option, DictOption):
                self._value_option = value_option
            else:
                raise InitializationError("Value option must be instance of one of base options except array and dict!")
        else:
            self._value_option = None

    def serialize(self, value):
        serializable_dict = {}
        if isinstance(self._value_option, BaseOption):
            for k, v in value.items():
                serialized_v = self._value_option.serialize(v)
                serializable_dict.update({k: serialized_v})
            return serializable_dict
        else:
            return value

    def deserialize(self, raw_value):
        try:
            if isinstance(self._value_option, BaseOption):
                deserialized_dict = {}
                for k, v in raw_value.items():
                    deserialized_dict.update({k: self._value_option.deserialize(v)})
                value = deserialized_dict
            else:
                value = raw_value
        except DeserializationError:
            raise DeserializationError("Unable to deserialize \"{}\" into dict for \"{}\"!".format(raw_value, self.name), raw_value, self.name)
        else:
            return value

    def serialize_json(self, value):
        if value is None:
            return json.dumps(None)
        elif self._value_option:
            return '{' + ', '.join(['{}: {}'.format(json.dumps(k), self._value_option.serialize_json(v)) for k, v in value.items()]) + '}'
        else:
            return json.dumps(value)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid JSON value for \"{}\": \"{}\"!".format(self.name, json_value), json_value, self.name)
        else:
            if value is not None:
                if not isinstance(value, dict):
                    raise DeserializationError("\"{}\" is not a JSON dict!".format(json_value), json_value, self.name)
                else:
                    if self._value_option:
                        return {k: self._value_option.deserialize_json(json.dumps(v)) for k, v in value.items()}
                    else:
                        return value
            else:
                return None

    def validate(self, value):
        super().validate(value)

        if not isinstance(value, dict):
            raise ValidationError("Invalid dict \"{}\" for \"{}\"!".format(value, self.name), value, self.name)
