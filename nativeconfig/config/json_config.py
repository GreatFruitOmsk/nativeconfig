from collections import OrderedDict
import json
import logging
from pathlib import Path

from nativeconfig.config.memory_config import MemoryConfig


LOG = logging.getLogger('nativeconfig')


class JSONConfig(MemoryConfig):
    """
    Store config in a JSON file as a dictionary. Fields are written in order of definition.

    @cvar JSON_PATH: Path to the config file.
    """
    LOG = LOG.getChild('JSONConfig')

    JSON_PATH = None

    def __init__(self):
        if not Path(self.JSON_PATH).is_file():
            with open(self.JSON_PATH, 'w+', encoding='utf-8') as f:
                f.write(json.dumps({}))

            _config = None
        else:
            with open(self.JSON_PATH, 'r', encoding='utf-8') as f:
                _config = json.load(f)

        super().__init__(initial_config=_config)

    #{ Private

    def _get_json_value(self, key):
        try:
            with open(self.JSON_PATH, 'r', encoding='utf-8') as f:
                try:
                    conf = json.load(f)
                    if key in conf:
                        return conf[key]
                    else:
                        self.LOG.info("Config file doesn't contain the key \"%s\".", key)
                except ValueError:
                    self.LOG.exception("Config file isn't valid:")
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    def _set_json_value(self, key, raw_value):
        try:
            with open(self.JSON_PATH, 'r+', encoding='utf-8') as f:
                conf = json.load(f)

                if raw_value is None:
                    conf.pop(key, None)
                else:
                    conf[key] = raw_value

                ordered_conf = OrderedDict()
                for m in self.options():
                    if m.name in conf:
                        ordered_conf[m.name] = conf.pop(m.name)

                f.seek(0)
                json.dump(ordered_conf, f, indent=4)
                f.truncate()
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    #{ BaseConfig

    def get_value(self, name, allow_cache=False):
        if allow_cache:
            return super().get_value(name, allow_cache)
        else:
            return self._get_json_value(name)

    def set_value(self, name, raw_value):
        super().set_value(name, raw_value)
        self._set_json_value(name, raw_value)

    def del_value(self, name):
        super().del_value(name)
        self._set_json_value(name, None)

    def get_array_value(self, name, allow_cache=False):
        if allow_cache:
            return super().get_array_value(name, allow_cache)
        else:
            return self.get_value(name)

    def set_array_value(self, name, value):
        super().set_array_value(name, value)
        self.set_value(name, value)

    def get_dict_value(self, name, allow_cache=False):
        if allow_cache:
            return super().get_dict_value(name, allow_cache)
        else:
            return self.get_value(name)

    def set_dict_value(self, name, value):
        super().set_dict_value(name, value)
        self.set_value(name, value)

    def reset_cache(self):
        super().reset_cache()

    #}
