import os
from pathlib import Path
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options import PathOption, StringOption, ArrayOption
from nativeconfig.options.dict_option import DictOption
from nativeconfig.options.float_option import FloatOption

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
        del c.path_dict
        del c.float_dict
        os.environ.pop('TEST_DICT', None)

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

    def test_json_serialization_deserialization_keeps_value(self):
        o = DictOption('test', value_option=PathOption('_', path_type=Path))
        v = {'a': Path('.'), 'b': Path('..')}
        j = o.serialize_json(v)
        self.assertEqual(o.deserialize_json(j), v)

    def test_json_serialization_of_None(self):
        o = DictOption('test', value_option=PathOption('_', path_type=Path))
        self.assertEqual(o.serialize_json(None), 'null')

    def test_json_deserialization_of_null(self):
        o = DictOption('test', value_option=PathOption('_', path_type=Path))
        self.assertEqual(o.deserialize_json('null'), None)

    def test_snapshot_can_be_restored(self):
        c = MyConfig.get_instance()
        v = {'a': Path('.'), 'b': Path('..')}
        c.path_dict = v
        s = c.snapshot()
        del c.path_dict
        self.assertNotEqual(c.path_dict, v)
        c.restore_snapshot(s)
        self.assertEqual(c.path_dict, v)
        return c

    def test_default_value_copied(self):
        default = {}

        class TestConfig(DummyMemoryConfig):
            dict_option = DictOption('DictOption', default=default, env_name='DICT_OPTION')

        c = TestConfig.get_instance()
        self.assertEqual(c.dict_option, {})
        default['question'] = 42
        self.assertEqual(c.dict_option, {})

    def test_choices_copied(self):
        value = {'key': 'value'}
        value2 = {'another_key': 'another_value'}
        choices = [value]

        class TestConfig(DummyMemoryConfig):
            dict_option = DictOption('DictOption', choices=choices, env_name='DICT_OPTION')

        c = TestConfig.get_instance()
        c.dict_option = {'key': 'value'}

        choices[0] = value2
        c.dict_option = {'key': 'value'}

        value['key'] = 'another_value'
        c.dict_option = {'key': 'value'}

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
        self.assertEqual(c.get_json_value_for_option_name('TestDict'), '{"Key1": "some_value"}')
        c.path_dict = {"key1": Path(".")}
        self.assertEqual(c.get_json_value_for_option_name('PathDict'), '{"key1": "."}')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_json_value_for_option_name('TestDict', '{"key1": "value1"}')
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_can_be_overridden_by_env(self):
        os.environ['TEST_DICT'] = '{"key1": "value1"}'
        c = MyConfig.get_instance()
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_json_value_for_option_name('TestDict', '{"key1": "value1"}')
        self.assertEqual(c.test_dict, {"key1": "value1"})

    def test_value_that_cannot_be_deserialized_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['TEST_DICT'] = '\"FORTYTWO\"'

        with self.assertRaises(DeserializationError):
            test_dict = c.test_dict

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_dict = c.test_dict
            self.assertEqual(test_dict, 'unresolved')

            os.environ['TEST_DICT'] = '{"key1": "value1"}'
            test_dict = c.test_dict
            self.assertEqual(test_dict, {"key1": "value1"})

    def test_invalid_deserialized_value_calls_resolver(self):
        class TestConfig(DummyMemoryConfig):
            dict_option = DictOption('DictOption', choices=[{"key1": "value1"}, {"key2": "value2"}], env_name='DICT_OPTION')

        c = TestConfig.get_instance()
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
        c.set_one_shot_json_value_for_option_name('TestDict', '{"3": "value1"}')

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

    def test_env_value_must_be_valid_json(self):
        os.environ['TEST_DICT'] = ']'

        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            test_dict = c.test_dict

        os.environ['TEST_DICT'] = '{"key3": "value3"}'
        self.assertEqual(c.test_dict, {"key3": "value3"})

    def test_json_value_is_of_expected_type(self):
        with self.assertRaises(DeserializationError):
            DictOption('_').deserialize_json("1")

#}
