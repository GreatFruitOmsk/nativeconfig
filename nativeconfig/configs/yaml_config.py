from collections import OrderedDict
import logging
from pathlib import Path
import yaml

from nativeconfig.configs.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')


class YAMLConfig(BaseConfig):
    """
    Store config in a YAML file as a dictionary. Fields are written in order of definition.

    @cvar YAML_PATH: Path to the config file.
    """
    LOG = LOG.getChild('YAMLConfig')

    YAML_PATH = None
    YAML_LOADER = yaml.CLoader if yaml.__with_libyaml__ else yaml.Loader
    YAML_DUMPER = yaml.CDumper if yaml.__with_libyaml__ else yaml.Dumper

    def __init__(self):
        if not Path(self.YAML_PATH).is_file():
            with open(self.YAML_PATH, 'w+', encoding='utf-8') as f:
                yaml.dump({}, f, Dumper=self.YAML_DUMPER)

        class OrderedDumper(self.YAML_DUMPER):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map',
                                                                                                data.items()))

        self.YAML_DUMPER = OrderedDumper

        super().__init__()

    #{ Private

    def _get_yaml_value(self, key):
        try:
            with Path(self.YAML_PATH).open('r', encoding='utf-8') as f:
                try:
                    conf = yaml.load(f, Loader=self.YAML_LOADER)
                    if key in conf:
                        return conf[key]
                    else:
                        self.LOG.info("Config file doesn't contain the key \"%s\".", key)
                except ValueError:
                    self.LOG.exception("Config file isn't valid:")
        except:
            self.LOG.exception("Unable to access config file:")

        return None

    def _set_yaml_value(self, key, raw_value):
        try:
            with Path(self.YAML_PATH).open('r+', encoding='utf-8') as f:
                conf = yaml.load(f, Loader=self.YAML_LOADER)

                if raw_value is None:
                    conf.pop(key, None)
                else:
                    conf[key] = raw_value

                ordered_conf = OrderedDict()
                for m in self.options():
                    if m.name in conf:
                        ordered_conf[m.name] = conf.pop(m.name)

                f.seek(0)
                yaml.dump(ordered_conf, f, Dumper=self.YAML_DUMPER)
                f.truncate()
        except:
            self.LOG.exception("Unable to access config file:")

    #{ BaseConfig

    def make_cache(self):
        with Path(self.YAML_PATH).open('r', encoding='utf-8') as f:
            return yaml.load(f, Loader=self.YAML_LOADER)

    def get_value_cache_free(self, name):
        return self._get_yaml_value(name)

    def set_value_cache_free(self, name, raw_value):
        self._set_yaml_value(name, raw_value)

    def del_value_cache_free(self, name):
        self._set_yaml_value(name, None)

    def get_array_value_cache_free(self, name):
        return self.get_value_cache_free(name)

    def set_array_value_cache_free(self, name, value):
        self.set_value_cache_free(name, value)

    def get_dict_value_cache_free(self, name):
        return self.get_value_cache_free(name)

    def set_dict_value_cache_free(self, name, value):
        self.set_value_cache_free(name, value)

    #}
