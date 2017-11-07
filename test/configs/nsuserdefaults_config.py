import unittest

try:
    from nativeconfig.configs import NSUserDefaultsConfig
except ImportError:
    pass
else:
    from test.configs import TestConfigMixin


    class MyNSUserDefaultsConfig(NSUserDefaultsConfig):
        pass


    class TestNSUserDefaultsConfig(TestConfigMixin, unittest.TestCase):
        CONFIG_TYPE = MyNSUserDefaultsConfig

        def tearDown(self):
            try:
                c = self.CONFIG_TYPE.get_instance()
                c.reset()
            except OSError:
                pass

            super().tearDown()

        def test_config_is_created_if_not_found(self):
            pass
