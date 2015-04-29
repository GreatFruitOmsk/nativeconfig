from nativeconfig.config.base_config import BaseConfig


class MemoryConfig(BaseConfig):
    def __init__(self):
        self._config = {}
        super().__init__()

    def get_value(self, key):
        return self._config.get(key, None)

    def set_value(self, key, value):
        if value is not None:
            self._config[key] = value
        else:
            self._config.pop(key, None)

    def del_value(self, key):
        self._config.pop(key, None)

    def get_array_value(self, key):
        return self._config.get(key, None)

    def set_array_value(self, key, value):
        if value is not None:
            self._config[key] = value
        else:
            self._config.pop(key, None)

    def get_dict_value(self, key):
        return self._config.get(key, None)

    def set_dict_value(self, key, value):
        if value is not None:
            self._config[key] = value
        else:
            self._config.pop(key, None)
