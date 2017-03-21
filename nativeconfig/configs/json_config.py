from collections import OrderedDict
import json
import logging
from pathlib import Path

from nativeconfig.configs.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')


class JSONConfig(BaseConfig):
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

        super().__init__()

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
                config = json.load(f)

                if raw_value is None:
                    config.pop(key, None)
                else:
                    config[key] = raw_value

                ordered_config = OrderedDict()

                # Ensure that current options are stored in order.
                for o in self.options():
                    if o.name in config:
                        ordered_config[o.name] = config.pop(o.name)
                    elif not len(config):
                        break

                # Everything else can appear in arbitrary order at the end.
                for k, v in config.items():
                    ordered_config[k] = v

                f.seek(0)
                json.dump(ordered_config, f, indent=4)
                f.truncate()
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    #{ BaseConfig

    def make_cache(self):
        with open(self.JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_value_cache_free(self, name):
        return self._get_json_value(name)

    def set_value_cache_free(self, name, raw_value):
        self._set_json_value(name, raw_value)

    def del_value_cache_free(self, name):
        self._set_json_value(name, None)

    def get_array_value_cache_free(self, name):
        return self.get_value_cache_free(name)

    def set_array_value_cache_free(self, name, value):
        self.set_value_cache_free(name, value)

    def get_dict_value_cache_free(self, name):
        return self.get_value_cache_free(name)

    def set_dict_value_cache_free(self, name, value):
        self.set_value_cache_free(name, value)

    #}
