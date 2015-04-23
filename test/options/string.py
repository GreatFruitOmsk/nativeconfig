import json
import os
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options import StringOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    name = StringOption('Name', default='Pheoktist')
    surname = StringOption('Surname', env_name='SURNAME')


class TestStringOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = StringOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.name
        del c.surname
        try:
            del os.environ['SURNAME']
        except KeyError:
            pass

#{ Custom

    def test_cannot_be_empty(self):
        c = MyConfig.get_instance()

        c.set_value('Name', "")
        self.assertEqual(c.name, 'Pheoktist')


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
        c.set_value_for_option_name('Name', "\"Вячеслав\"")
        self.assertEqual(c.name, "Вячеслав")

    def test_value_can_be_overridden_by_env(self):
        os.environ['SURNAME'] = json.dumps(str("李".encode('utf-8')))
        c = MyConfig.get_instance()
        self.assertEqual(c.surname, "李")

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Name', "\"Валентина\"")
        self.assertEqual(c.name, "Валентина")

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['SURNAME'] = "1"

        with self.assertRaises(DeserializationError):
            surname = c.surname

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            surname = c.surname
            self.assertEqual(surname, 'unresolved')

            os.environ['SURNAME'] = json.dumps(str("李".encode('utf-8')))
            surname = c.surname
            self.assertEqual(surname, "李")

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class StringOptions(DummyMemoryConfig):
             string_option = StringOption('StringOption', choices=["String 1", "String 2"], env_name='STRING_OPTION', default="String 1")

        c = StringOptions.get_instance()
        os.environ['STRING_OPTION'] = json.dumps(str("String 3".encode('utf-8')))

        with self.assertRaises(ValidationError):
            string_option = c.string_option

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            string_option = c.string_option
            self.assertEqual(string_option, 'unresolved')

            os.environ['STRING_OPTION'] = json.dumps(str("String 2".encode('utf-8')))
            string_option = c.string_option
            self.assertEqual(string_option, "String 2")

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Name', '\"Владислав\"')

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

    def test_env_is_first_json_deserialized_then_deserialized(self):
        c = MyConfig.get_instance()
        os.environ['SURNAME'] = json.dumps(str("李".encode('utf-8')))
        with patch.object(StringOption, 'deserialize_json', return_value="b\'\\xe6\\x9d\\x8e\'") as mock_deserialize_json:
            surname = c.surname

        with patch.object(StringOption, 'deserialize', return_value="李") as mock_deserialize:
            surname = c.surname

        mock_deserialize_json.assert_called_with('"b\'\\\\xe6\\\\x9d\\\\x8e\'"')
        mock_deserialize.assert_called_with("b\'\\xe6\\x9d\\x8e\'")

    def test_env_value_must_be_valid_json(self):
        os.environ['SURNAME'] = "]"
        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            surname = c.surname
#}
