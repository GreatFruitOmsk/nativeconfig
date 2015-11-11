from copy import deepcopy

from nativeconfig.config.base_config import BaseConfig


class MemoryConfig(BaseConfig):
    """
    Store config in in-memory dict.
    """
    def __init__(self, initial_config=None):
        """
        @param initial_config: Initial state of the memory config.
        @type initial_config: dict or None
        """
        self._config = deepcopy(initial_config) if initial_config else {}
        super().__init__()

    def get_value(self, name, allow_cache=False):
        return self._config.get(name, None)

    def set_value(self, name, raw_value):
        if raw_value is not None:
            self._config[name] = raw_value
        else:
            self._config.pop(name, None)

    def del_value(self, name):
        self._config.pop(name, None)

    def get_array_value(self, name, allow_cache=False):
        return self._config.get(name, None)

    def set_array_value(self, name, value):
        if value is not None:
            self._config[name] = value
        else:
            self._config.pop(name, None)

    def get_dict_value(self, name, allow_cache=False):
        return self._config.get(name, None)

    def set_dict_value(self, name, value):
        if value is not None:
            self._config[name] = value
        else:
            self._config.pop(name, None)

    def reset_cache(self):
        self._config = {}
