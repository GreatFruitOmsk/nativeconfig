import os
from pathlib import Path
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options import PathOption, StringOption, ArrayOption
from nativeconfig.options.dict import DictOption
from nativeconfig.options.float import FloatOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    test_dict = DictOption('TestDict', env_name='TEST_DICT', default={"key1": "value1", "key2": "value2"})
    path_dict = DictOption('PathDict', value_option=PathOption('PathOption', path_type=Path))
    float_dict = DictOption('FloatDict', value_option=FloatOption('FloatOption'))


class TestDictOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = DictOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.test_dict
        try:
            del os.environ['TEST_DICT']
        except KeyError:
            pass

#{ Custom

    def test_value_option_must_be_instance_of_base_option(self):
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('DictOption', value_option=str)
        c = MyConfig.get_instance()
        c.array_option = self.OPTION_TYPE('DictOption', value_option=StringOption("test"))

    def test_value_option_must_not_be_array_or_dict(self):
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('DictOption', value_option=ArrayOption('test'))
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('DictOption', value_option=DictOption('test'))

    def test_option_raises_deserialization_error_if_value_option_invalid(self):
        c = MyConfig.get_instance()
        with self.assertRaises(DeserializationError):
            c.float_dict = {"Key": "not_float"}
            float_dict = c.float_dict

#{ TestOptionMixin

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = DictOption('EmptyChoices', choices=[])

    def test_default_value_must_be_one_of_choices_if_any(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                dict_option = self.OPTION_TYPE('DictOption', choices=[{"key1": "value1", "key2": "value2"}], default={"key1": "value1", "key2": "value3"})

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                dict_option = self.OPTION_TYPE('DictOption', choices=[{"key1": "value1", "key2": "value2"}, 1])

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                dict_option = self.OPTION_TYPE('DictOption', default='super dict')

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            dict_option = self.OPTION_TYPE('DictOption', choices=[{"key1": "value1"}, {"key2": "value2"}])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().dict_option = {"key1": "value2"}

        MyConfig.get_instance().dict_option = {"key1": "value1"}
        MyConfig.get_instance().dict_option = {"key2": "value2"}

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.test_dict = {"Key1": "some_value"}
        self.assertEqual(c.get_value_for_option_name('TestDict'), '{"Key1": "some_value"}')
        c.path_dict = {"key1": Path(".")}
        self.assertEqual(c.get_value_for_option_name('PathDict'), '{"key1": "."}')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('TestDict', '{"key1": "value1"}')
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_can_be_overridden_by_env(self):
        os.environ['TEST_DICT'] = '{"key1": "value1"}'
        c = MyConfig.get_instance()
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('TestDict', '{"key1": "value1"}')
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['TEST_DICT'] = '\"FORTYTWO\"'

        with self.assertRaises(ValidationError):
            test_dict = c.test_dict

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_dict = c.test_dict
            self.assertEqual(test_dict, 'unresolved')

            os.environ['TEST_DICT'] = '{"key1": "value1"}'
            test_dict = c.test_dict
            self.assertEqual(test_dict, {"key1": "value1"})

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class Dicts(DummyMemoryConfig):
            dict_option = DictOption('DictOption', choices=[{"key1": "value1"}, {"key2": "value2"}], env_name='DICT_OPTION')

        c = Dicts.get_instance()
        os.environ['DICT_OPTION'] = '{"key1": "value2"}'

        with self.assertRaises(ValidationError):
            dict_option = c.dict_option

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            dict_option = c.dict_option
            self.assertEqual(dict_option, 'unresolved')

            os.environ['DICT_OPTION'] = '{"key1": "value1"}'
            dict_option = c.dict_option
            self.assertEqual(dict_option, {"key1": "value1"})

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('TestDict', '{"3": "value1"}')

        c.test_dict = {"key1": "value1"}
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.test_dict = "super dict"

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.test_dict = {"key1": "value4"}
        c.test_dict = None
        self.assertEqual(c.test_dict, {"key1": "value1", "key2": "value2"})

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.test_dict
        self.assertEqual(c.test_dict, {"key1": "value1", "key2": "value2"})

    def test_env_is_first_json_deserialized_then_deserialized(self):
        class Dicts(DummyMemoryConfig):
            dict_option = DictOption('DictOption', env_name='DICT_OPTION')

        os.environ['DICT_OPTION'] = '{"key2": "value2"}'
        c = Dicts.get_instance()

        with patch.object(DictOption, 'deserialize_json', return_value={"key2": "value2"}) as mock_deserialize_json:
            dict_option = c.dict_option

        with patch.object(DictOption, 'deserialize', return_value={"key2": "value2"}) as mock_deserialize:
            dict_option = c.dict_option

        mock_deserialize_json.assert_called_with('{"key2": "value2"}')
        mock_deserialize.assert_called_with({"key2": "value2"})

    def test_env_value_must_be_valid_json(self):
        os.environ['TEST_DICT'] = ']'
        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            test_dict = c.test_dict

#}
