import collections
import json
import os
import tempfile
import unittest
import unittest.mock

from nativeconfig.config.json_config import JSONConfig
from nativeconfig.options import StringOption, IntOption, ArrayOption, DictOption

from test.config import TestConfigMixin


class MyJSONConfig(JSONConfig):
    JSON_PATH = tempfile.mktemp("_test.json")


class TestJSONConfig(unittest.TestCase, TestConfigMixin):
    CONFIG_TYPE = MyJSONConfig

    def tearDown(self):
        try:
            os.unlink(MyJSONConfig.JSON_PATH)
        except FileNotFoundError:
            pass

        TestConfigMixin.tearDown(self)

    def test_exception_is_suppressed_if_config_is_not_accessible(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        os.unlink(c.JSON_PATH)
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Ilya')

    def test_get_value_returns_None_if_json_file_is_malformed(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')

        with open(c.JSON_PATH, 'w') as f:
            f.write("hello world")
            f.flush()

        self.assertEqual(c.get_value('FirstName'), None)

    def test_config_is_created_if_not_found(self):
        class MyConfig(MyJSONConfig):
            first_name = StringOption('FirstName', default='Ilya')

        self.assertEqual(os.path.isfile(MyConfig.JSON_PATH), False)
        MyConfig.get_instance()
        self.assertEqual(os.path.isfile(MyConfig.JSON_PATH), True)

    def test_order_is_preserved_in_json(self):
        class MyConfig(MyJSONConfig):
            second_name = StringOption('SecondName', default='Kulakov')
            age = IntOption('Age', default=42)
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        c.second_name = 'Martynovich'
        c.age = 9000

        d = json.load(open(MyConfig.JSON_PATH, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
        keys = list(d.keys())

        i = keys.index('SecondName')
        self.assertEqual(i + 1, keys.index('Age'))
        self.assertEqual(i + 2, keys.index('FirstName'))
