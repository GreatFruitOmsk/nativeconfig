import unittest

from nativeconfig.config import MemoryConfig
from test.config import TestConfigMixin


class MyMemoryConfig(MemoryConfig):
    pass


class TestMemoryConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = MyMemoryConfig

    def test_config_is_created_if_not_found(self):
        pass
