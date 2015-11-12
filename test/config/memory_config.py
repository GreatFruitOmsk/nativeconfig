import unittest

from nativeconfig.config import MemoryConfig
from test.config import TestConfigMixin


class MyMemoryConfig(MemoryConfig):
    pass


class TestMemoryConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = MyMemoryConfig

    def test_config_is_created_if_not_found(self):
        pass

    def test_initial_config(self):
        c = MyMemoryConfig(initial_config={'a': 42})
        self.assertEqual(c.get_value('a'), 42)

    def test_get_value_returns_cached_value_if_allowed(self):
        pass

    def test_get_array_value_returns_cached_value_if_allowed(self):
        pass

    def test_get_dict_value_returns_cached_value_if_allowed(self):
        pass

    def test_reset_cache(self):
        pass

    def test_set_value_updates_cached_value(self):
        pass

    def test_set_array_value_updates_cached_value(self):
        pass

    def test_set_dict_value_updated_cached_value(self):
        pass

    def test_del_value_deletes_cached_value(self):
        pass
