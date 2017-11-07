import os
import tempfile
import unittest
import yaml

from nativeconfig.configs.yaml_config import YAMLConfig
from nativeconfig.options import StringOption, IntOption

from . import TestConfigMixin


class TestYAMLConfigMixin(TestConfigMixin):
    def tearDown(self):
        try:
            os.unlink(MyYAMLConfig.YAML_PATH)
        except FileNotFoundError:
            pass

        super().tearDown()

    def test_exception_is_suppressed_if_config_is_not_accessible(self):
        class MyConfig(MyYAMLConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        os.unlink(c.YAML_PATH)
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Ilya')

    def test_get_value_returns_None_if_yaml_file_is_malformed(self):
        class MyConfig(MyYAMLConfig):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')

        with open(c.YAML_PATH, 'w') as f:
            f.write("{hello world")
            f.flush()

        self.assertEqual(c.get_value('FirstName'), None)

    def test_config_is_created_if_not_found(self):
        class MyConfig(MyYAMLConfig):
            first_name = StringOption('FirstName', default='Ilya')

        self.assertEqual(os.path.isfile(MyConfig.YAML_PATH), False)
        MyConfig.get_instance()
        self.assertEqual(os.path.isfile(MyConfig.YAML_PATH), True)

    def test_order_is_preserved_in_yaml(self):
        class MyConfig(MyYAMLConfig):
            second_name = StringOption('SecondName', default='Kulakov')
            age = IntOption('Age', default=42)
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        c.second_name = 'Martynovich'
        c.age = 9000

        data = open(MyConfig.YAML_PATH, encoding='utf-8').read()

        second_name_index = data.index('SecondName')
        age_index = data.index('Age')
        first_name_index = data.index('FirstName')

        self.assertLess(second_name_index, age_index)
        self.assertLess(age_index, first_name_index)


class MyYAMLConfig(YAMLConfig):
    YAML_PATH = tempfile.mktemp("_test.yml")
    YAML_LOADER = yaml.Loader
    YAML_DUMPER = yaml.Dumper


class MyCYAMLConfig(YAMLConfig):
    YAML_PATH = tempfile.mktemp("_test.yml")
    YAML_LOADER = yaml.CLoader
    YAML_DUMPER = yaml.CDumper


class TestYAMLConfig(TestYAMLConfigMixin, unittest.TestCase):
    CONFIG_TYPE = MyYAMLConfig


class TestCYAMLConfig(TestYAMLConfigMixin, unittest.TestCase):
    CONFIG_TYPE = MyCYAMLConfig
