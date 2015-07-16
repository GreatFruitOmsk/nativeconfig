import json
from nativeconfig.exceptions import DeserializationError, ValidationError, InitializationError
from nativeconfig.options.base_option import BaseOption


class ArrayOption(BaseOption):
    """
    ArrayOption represents Python arrays in config. ArrayOption can contain other Options as elements
    """
    def __init__(self, name, value_option=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.

        @param value_option: An instance of BaseOption subclass that provides serialization
                             and validation.
        @type value_option: BaseOption
        """
        super().__init__(name, setter='set_array_value', getter='get_array_value',  **kwargs)
        if value_option:
            from nativeconfig.options.dict_option import DictOption

            if isinstance(value_option, BaseOption) and not isinstance(value_option, ArrayOption) and not isinstance(value_option, DictOption):
                self._value_option = value_option
            else:
                raise InitializationError("Value option must be an instance BaseOption except ArrayOption and DictOption!")
        else:
            self._value_option = None

    def serialize(self, value):
        if self._value_option:
            serializable_list = []
            for i in value:
                serializable_list.append(self._value_option.serialize(i))
            return serializable_list
        else:
            return value

    def deserialize(self, raw_value):
        try:
            if self._value_option:
                deserialized_list = []
                for i in raw_value:
                    deserialized_list.append(self._value_option.deserialize(i))

                value = deserialized_list
            else:
                value = raw_value
        except DeserializationError:
            raise DeserializationError("Unable to deserialize \"{}\" into array for \"{}\"!".format(raw_value, self.name), raw_value, self.name)
        else:
            return value

    def serialize_json(self, value):
        if value is None:
            return json.dumps(None)
        elif self._value_option:
            # A JSON array of JSON-serialized values must be constructed manually
            # to avoid double-serialization.
            return '[' + ', '.join([self._value_option.serialize_json(v) for v in value]) + ']'
        else:
            return json.dumps(value)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid JSON value for \"{}\": \"{}\"!".format(self.name, json_value), json_value, self.name)
        else:
            if value is not None:
                if not isinstance(value, list):
                    raise DeserializationError("\"{}\" is not a JSON array!".format(json_value), json_value, self.name)
                else:
                    if self._value_option:
                        return [self._value_option.deserialize_json(json.dumps(v)) for v in value]
                    else:
                        return value
            else:
                return None

    def validate(self, value):
        super().validate(value)

        if not isinstance(value, (list, tuple)):
            raise ValidationError("Invalid array \"{}\" for \"{}\"!".format(value, self.name), value, self.name)
