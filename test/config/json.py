import os
import unittest

from nativeconfig.config.json import JSONConfig
from nativeconfig.options.string import StringOption

from test.config import TestConfigMixin


class JSONConfig(JSONConfig):
    CONFIG_PATH = '/tmp/test_config.json'


class TestJSONConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = JSONConfig

    def tearDown(self):
        try:
            os.unlink(JSONConfig.CONFIG_PATH)
        except FileNotFoundError:
            pass

        TestConfigMixin.tearDown(self)

    def test_exception_is_suppressed_if_config_is_not_accessible(self):
        class MyConfig(JSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        os.unlink(c.CONFIG_PATH)
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Ilya')

    def test_get_value_returns_None_if_json_file_is_malformed(self):
        class MyConfig(JSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')

        with open(c.CONFIG_PATH, 'w') as f:
            f.write("hello world")
            f.flush()

        self.assertEqual(c.get_value('FirstName'), None)
