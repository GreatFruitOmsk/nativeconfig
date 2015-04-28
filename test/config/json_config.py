import os
import unittest

from nativeconfig.config.json_config import JSONConfig
from nativeconfig.options.string_option import StringOption

from test.config import TestConfigMixin


class MyJSONConfig(JSONConfig):
    CONFIG_PATH = '/tmp/test_config.json'


class TestJSONConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = MyJSONConfig

    def tearDown(self):
        try:
            os.unlink(MyJSONConfig.CONFIG_PATH)
        except FileNotFoundError:
            pass

        TestConfigMixin.tearDown(self)

    def test_exception_is_suppressed_if_config_is_not_accessible(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        os.unlink(c.CONFIG_PATH)
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Ilya')

    def test_get_value_returns_None_if_json_file_is_malformed(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')

        with open(c.CONFIG_PATH, 'w') as f:
            f.write("hello world")
            f.flush()

        self.assertEqual(c.get_value('FirstName'), None)

    def test_config_is_created_if_not_found(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        self.assertEqual(os.path.isfile(MyConfig.CONFIG_PATH), False)
        MyConfig.get_instance()
        self.assertEqual(os.path.isfile(MyConfig.CONFIG_PATH), True)
