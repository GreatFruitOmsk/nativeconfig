import unittest
import unittest.mock
import sys

if sys.platform.startswith('win32'):
    import winreg

    from nativeconfig.configs import RegistryConfig
    from nativeconfig.configs.registry_config import traverse_registry_key
    from nativeconfig.options import StringOption, ArrayOption, DictOption

    from test.configs import TestConfigMixin

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
