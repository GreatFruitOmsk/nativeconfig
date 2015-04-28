from nativeconfig.config.base_config import BaseConfig


class MemoryConfig(BaseConfig):
    def __init__(self):
        self._config = {}
        super().__init__()

    def get_value(self, key):
        v = self._config.get(key, None)
        return str(v) if v is not None else None

    def set_value(self, key, value):
        self._config[key] = str(value)

    def del_value(self, key):
        self._config.pop(key, None)

    def get_array_value(self, key):
        v = self._config.get(key, None)
        return [str(i) for i in v] if v is not None else None

    def set_array_value(self, key, value):
        self._config[key] = [str(v) for v in value]

    def get_dict_value(self, key):
        v = self._config.get(key, None)
        return {str(k): str(i) for k, i in v.items()} if v is not None else None

    def set_dict_value(self, key, value):
        self._config[key] = {str(k): str(v) for k, v in value.items()}
