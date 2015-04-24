import unittest
import sys

if sys.platform.startswith('win32'):
    from nativeconfig.config import RegistryConfig
    from test.config import TestConfigMixin

    class RegistryConfig(RegistryConfig):
        CONFIG_PATH = r'Software\test_config'

    class TestRegistryConfig(unittest.TestCase, TestConfigMixin):
        CONFIG_TYPE = RegistryConfig
