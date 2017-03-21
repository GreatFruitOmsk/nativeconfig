from collections import OrderedDict

from .memory_config import MemoryConfig
from nativeconfig.options import ValueSource


class ChainConfig:
    @classmethod
    def make_temporary_config(cls, options):
        return type('TemporaryConfig', (MemoryConfig,), options)()

    def __init__(self, configs):
        """
        @type configs: {BaseConfig}
        """
        if not isinstance(configs, OrderedDict):
            raise ValueError("configs must be an OrderedDict to preserve resolution order")

        self._configs_by_name = {}
        self._configs_by_attribute = {}
        options = {}

        for c in configs.values():
            for attribute_name, option in c._ordered_options_by_attribute.items():
                self._configs_by_attribute.setdefault(attribute_name, []).append(c)
                self._configs_by_name.setdefault(option.name, []).append(c)

                if attribute_name not in options:
                    options[attribute_name] = option
                else:
                    current_option = options[attribute_name]

                    if current_option.name != option.name:
                        raise ValueError("name mismatch: expected '{}' but found '{}' in '{}'".format(
                            current_option.name, option.name, c
                        ))
                    elif not isinstance(option, current_option.__class__):
                        # Foremost configs be specialized options of inferior.
                        raise ValueError("type mismatch: expected a subclass of '{}' but found '{}' in '{}'".format(
                            current_option.__class__.__name__, option.__class__.__name__, c
                        ))

        self._temporary = self.make_temporary_config(options)

    @property
    def temporary(self):
        """
        @rtype: MemoryConfig
        """
        return self._temporary

    def __getattr__(self, name):
        if name not in self._configs_by_attribute:
            raise AttributeError("'{}' has no attribute '{}'", self.__class__.__name__, name)

        value, source = self._temporary._ordered_options_by_attribute[name].read_value(self._temporary)
        if source != ValueSource.default and value is not None:
            return value

        default = None

        for c in self._configs_by_attribute[name]:
            option = c._ordered_options_by_attribute[name]
            value, source = option.read_value(c)

            if source != ValueSource.default:
                return value
            elif default is None:
                default = value
        else:
            return default
