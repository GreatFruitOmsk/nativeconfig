import json
import os
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options import StringOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    name = StringOption('Name', allow_empty=False, default='Pheoktist')
    surname = StringOption('Surname', env_name='SURNAME')
    test_string = StringOption('TestString', env_name='TEST_STRING', choices=['str1', 'str2'], default='str1')
    empty_string = StringOption('EmptyString')


class TestStringOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = StringOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.name
        del c.surname
        os.environ.pop('SURNAME', None)

#{ Custom

    def test_cannot_be_empty_if_disallowed(self):
        c = MyConfig.get_instance()

        c.set_value('Name', "")
        self.assertEqual(c.name, 'Pheoktist')

    def test_can_be_empty_if_allowed(self):
        c = MyConfig.get_instance()
        c.empty_string = ''
        empty_string = c.empty_string
        self.assertEqual(empty_string, '')

#{ TestOptionMixin

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = StringOption('EmptyChoices', choices=[])

    def test_default_value_must_be_one_of_choices_if_any(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                string_value = self.OPTION_TYPE('String', choices=["string 1", "string 2"], default="string 3")

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                string_value = self.OPTION_TYPE('String', choices=["String 1", 123, 'String 3'])

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                string_value = self.OPTION_TYPE('String', default=1)

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            string_value = self.OPTION_TYPE('String', choices=["String 1", "String 2"])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().string_value = "String 3"

        MyConfig.get_instance().string_value = "String 1"
        MyConfig.get_instance().string_value = "String 2"

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.name = "Василий"
        self.assertEqual(c.name, "Василий")

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_json_value_for_option_name('Name', "\"Вячеслав\"")
        self.assertEqual(c.name, "Вячеслав")

    def test_value_can_be_overridden_by_env(self):
        os.environ['SURNAME'] = json.dumps("李")
        c = MyConfig.get_instance()
        self.assertEqual(c.surname, "李")

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_json_value_for_option_name('Name', "\"Валентина\"")
        self.assertEqual(c.name, "Валентина")

    def test_value_that_cannot_be_deserialized_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['TEST_STRING'] = json.dumps('str3')

        with self.assertRaises(ValidationError):
            test_string = c.test_string

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_string = c.test_string
            self.assertEqual(test_string, 'unresolved')

            os.environ['TEST_STRING'] = json.dumps('str2')
            test_string = c.test_string
            self.assertEqual(test_string, 'str2')

    def test_invalid_deserialized_value_calls_resolver(self):
        class StringOptions(DummyMemoryConfig):
             string_option = StringOption('StringOption', choices=["String 1", "String 2"], env_name='STRING_OPTION', default="String 1")

        c = StringOptions.get_instance()
        os.environ['STRING_OPTION'] = json.dumps("String 3")

        with self.assertRaises(ValidationError):
            string_option = c.string_option

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            string_option = c.string_option
            self.assertEqual(string_option, 'unresolved')

            os.environ['STRING_OPTION'] = json.dumps("String 2")
            string_option = c.string_option
            self.assertEqual(string_option, "String 2")

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_json_value_for_option_name('Name', '\"Владислав\"')

        c.name = "Вера"
        self.assertEqual(c.name, "Вера")

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.name = 1

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.name = "Всеволод"
        c.name = None
        self.assertEqual(c.name, "Pheoktist")

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.name
        self.assertEqual(c.name, "Pheoktist")

    def test_env_value_must_be_valid_json(self):
        os.environ['SURNAME'] = "]"

        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            surname = c.surname

        os.environ['SURNAME'] = '"Appleseed"'
        self.assertEqual(c.surname, 'Appleseed')

    def test_json_value_is_of_expected_type(self):
        with self.assertRaises(DeserializationError):
            StringOption('_').deserialize_json("1")

#}
