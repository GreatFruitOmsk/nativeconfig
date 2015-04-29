import unittest
import sys

if sys.platform.startswith('win32'):
    import winreg

    from nativeconfig.config import RegistryConfig
    from nativeconfig.config.registry_config import traverse_registry_key
    from nativeconfig.options import StringOption

    from test.config import TestConfigMixin

    class MyRegistryConfig(RegistryConfig):
        REGISTRY_PATH = r'Software\test_config'

    class TestRegistryConfig(unittest.TestCase, TestConfigMixin):
        CONFIG_TYPE = MyRegistryConfig

        def tearDown(self):
            try:
                for k in traverse_registry_key(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH):
                    winreg.DeleteKey(MyRegistryConfig.REGISTRY_KEY, k)
            except OSError:
                pass

            TestConfigMixin.tearDown(self)

        def test_config_is_created_if_not_found(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            with self.assertRaises(FileNotFoundError):
                winreg.OpenKey(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH)

            MyConfig.get_instance()

            winreg.OpenKey(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH)
