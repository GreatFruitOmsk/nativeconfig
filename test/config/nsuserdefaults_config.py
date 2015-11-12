import sys
import unittest

if sys.platform.startswith('darwin'):
    from nativeconfig.config import NSUserDefaultsConfig
    from test.config import TestConfigMixin


    class MyNSUserDefaultsConfig(NSUserDefaultsConfig):
        pass


    class TestNSUserDefaultsConfig(unittest.TestCase, TestConfigMixin):
        CONFIG_TYPE = MyNSUserDefaultsConfig

        def tearDown(self):
            try:
                c = self.CONFIG_TYPE.get_instance()
                c.reset()
            except OSError:
                pass

            TestConfigMixin.tearDown(self)

        def test_config_is_created_if_not_found(self):
            pass

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
