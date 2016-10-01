from copy import deepcopy

from nativeconfig.configs.base_config import BaseConfig


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

    #{ BaseConfig

    def make_cache(self):
        return deepcopy(self._config)

    def get_value_cache_free(self, name):
        return self._config.get(name, None)

    def set_value_cache_free(self, name, raw_value):
        if raw_value is not None:
            self._config[name] = raw_value
        else:
            self._config.pop(name, None)

    def del_value_cache_free(self, name):
        self._config.pop(name, None)

    def get_array_value_cache_free(self, name):
        return self._config.get(name, None)

    def set_array_value_cache_free(self, name, value):
        if value is not None:
            self._config[name] = value
        else:
            self._config.pop(name, None)

    def get_dict_value_cache_free(self, name):
        return self._config.get(name, None)

    def set_dict_value_cache_free(self, name, value):
        if value is not None:
            self._config[name] = value
        else:
            self._config.pop(name, None)

    #}
