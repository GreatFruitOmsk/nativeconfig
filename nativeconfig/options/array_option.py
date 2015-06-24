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
        """
        super().__init__(name, setter='set_array_value', getter='get_array_value',  **kwargs)
        if value_option:
            from nativeconfig.options.dict_option import DictOption

            if isinstance(value_option, BaseOption) \
            and not isinstance(value_option, ArrayOption) \
            and not isinstance(value_option, DictOption):
                self._value_option = value_option
            else:
                raise InitializationError("Value option must be instance of one of base options except array and dict")
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
            raise DeserializationError("Unable to deserialize \"{}\" into array for \"{}\"!".format(raw_value, self._name), raw_value, self._name)
        else:
            return value

    def serialize_json(self, value):
        serializable_list = []
        if self._value_option:
            for i in value:
                serializable_list.append(self._value_option.serialize(i))
            return json.dumps(serializable_list)
        else:
            return json.dumps(value)

    def deserialize_json(self, json_value):
        try:
            value = json.loads(json_value)
        except ValueError:
            raise DeserializationError("Invalid json for \"{}\": \"{}\"!".format(self._name, json_value), json_value, self._name)
        else:
            return value

    def validate(self, value):
        super().validate(value)
        if type(value) == list:
            return
        else:
            raise ValidationError("Invalid array \"{}\" for \"{}\"!".format(value, self._name), value, self._name)
