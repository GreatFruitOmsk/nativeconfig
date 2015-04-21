import json
from nativeconfig.exceptions import DeserializationError, ValidationError
from nativeconfig.options.base import BaseOption


class ArrayOption(BaseOption):
    """
    ArrayOption represents Python arrays in config. ArrayOption can contain other Options as elements

    """

    def __init__(self, name, value_option=None, **kwargs):
        """
        Accepts all the arguments of BaseConfig except choices.
        """
        super().__init__(name, **kwargs)
        self._value_option = value_option

    def serialize(self, value):
        serializable_list = []
        if isinstance(self._value_option, BaseOption):
            for i in value:
                serializable_list.append(self._value_option.serialize(i))
            return str(serializable_list)
        else:
            return str(value)

    def deserialize(self, raw_value):
        if type(raw_value) == list:
            return raw_value
        else:
            try:
                raw_list = list(eval(raw_value))
                if isinstance(self._value_option, BaseOption):
                    deserizlized_list = []
                    for i in raw_list:
                        deserizlized_list.append(self._value_option.deserialize(i))
                    value = deserizlized_list
                else:
                    value = raw_list
            except (ValueError, TypeError, NameError):
                raise DeserializationError("Unable to deserialize '{}' into array.".format(raw_value), raw_value)
            else:
                return value

    def serialize_json(self, value):
        serializable_list = []
        if isinstance(self._value_option, BaseOption):
            for i in value:
                serializable_list.append(self._value_option.serialize(i))
            return json.dumps(serializable_list)
        else:
            return json.dumps(value)

    def validate(self, value):
        super().validate(value)
        if type(value) == list:
            return
        else:
            raise ValidationError("Invalid array '{}'.".format(value), value)
