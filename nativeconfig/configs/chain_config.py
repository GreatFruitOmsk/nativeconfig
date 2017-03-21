from collections import OrderedDict

from nativeconfig.options import ValueSource


class ChainConfig:
    def __init__(self, configs):
        """
        @type configs: {BaseConfig}
        """
        if not isinstance(configs, OrderedDict):
            raise ValueError("configs must be an OrderedDict to preserve resolution order")

        self._configs_by_name = {}
        self._configs_by_attribute = {}

        for c in configs.values():
            for name in c._ordered_options_by_name.keys():
                self._configs_by_name.setdefault(name, []).append(c)

            for attribute_name in c._ordered_options_by_attribute.keys():
                self._configs_by_attribute.setdefault(attribute_name, []).append(c)

        for name, config in configs.items():
            setattr(self, name, config)

    def __getattr__(self, name):
        if name not in self._configs_by_attribute:
            raise AttributeError("'{}' has no attribute '{}'", self.__class__.__name__, name)

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
