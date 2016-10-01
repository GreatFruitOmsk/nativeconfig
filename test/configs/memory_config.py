import unittest

from nativeconfig.options import IntOption
from nativeconfig.configs import MemoryConfig

from test.configs import TestConfigMixin


class MyMemoryConfig(MemoryConfig):
    pass


class TestMemoryConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = MyMemoryConfig

    def test_config_is_created_if_not_found(self):
        pass

    def test_inital_config(self):
        class MyConfig(MemoryConfig):
            age = IntOption('Age', default=42)

        c = MyConfig({'Age': 9000})
        self.assertEqual(c.age, 9000)

        c.reset()
        self.assertEqual(c.age, 42)
