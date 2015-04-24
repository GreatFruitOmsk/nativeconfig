import os
from pathlib import Path
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options.array import ArrayOption
from nativeconfig.options.dict import DictOption
from nativeconfig.options.float import FloatOption
from nativeconfig.options.path import PathOption
from nativeconfig.options.string import StringOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    test_array = ArrayOption('TestArray', env_name='TEST_ARRAY', default=["1", "2", "3"])
    path_array = ArrayOption('PathArray', value_option=PathOption('PathOption', path_type=Path, choices=[Path("."), Path("..")]))
    float_array = ArrayOption('FloatArray', value_option=FloatOption('FloatOption'))


class TestArrayOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = ArrayOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.test_array
        try:
            del os.environ['TEST_ARRAY']
        except KeyError:
            pass

#{ Custom

    def test_value_option_must_be_instance_of_base_option(self):
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('ArrayOption1', value_option=str)
        c = MyConfig.get_instance()
        c.array_option = self.OPTION_TYPE('ArrayOption1', value_option=StringOption("test"))

    def test_value_option_must_not_be_array_or_dict(self):
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('ArrayOption2', value_option=ArrayOption('test'))
        with self.assertRaises(InitializationError):
            c = MyConfig.get_instance()
            c.array_option = self.OPTION_TYPE('ArrayOption2', value_option=DictOption('test'))

    def test_option_raises_deserialization_error_if_value_option_invalid(self):
        c = MyConfig.get_instance()
        with self.assertRaises(DeserializationError):
            c.float_array = ["not_float"]
            float_array = c.float_array

#{ TestOptionMixin

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = ArrayOption('EmptyChoices', choices=[])

    def test_default_value_must_be_one_of_choices_if_any(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                array_option = self.OPTION_TYPE('ArrayOption', choices=[[1, 2, 3], ["1", "2", "3"]], default=[1])

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                array_option = self.OPTION_TYPE('ArrayOption', choices=[[1, 2, 3], "1, 2, 3"])

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                array_option = self.OPTION_TYPE('ArrayOption', default='[1, 2, 3]')

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            array_option = self.OPTION_TYPE('ArrayOption', choices=[[1], [2], [3]])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().array_option = ["1"]

        MyConfig.get_instance().array_option = [1]
        MyConfig.get_instance().array_option = [2]
        MyConfig.get_instance().array_option = [3]

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.test_array = ["1", "2", "3"]
        self.assertEqual(c.get_value_for_option_name('TestArray'), '["1", "2", "3"]')
        c.path_array = [Path("."), Path("..")]
        self.assertEqual(c.get_value_for_option_name('PathArray'), '[".", ".."]')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('TestArray', '["1", "2", "3"]')
        self.assertEqual(c.test_array, ["1", "2", "3"])

    def test_value_can_be_overridden_by_env(self):
        os.environ['TEST_ARRAY'] = '[1, 2, "3"]'
        c = MyConfig.get_instance()
        self.assertEqual(c.test_array, [1, 2, "3"])

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('TestArray', '["1"]')
        self.assertEqual(c.test_array, ["1"])

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['TEST_ARRAY'] = '\"FORTYTWO\"'

        with self.assertRaises(ValidationError):
            test_array = c.test_array

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_array = c.test_array
            self.assertEqual(test_array, 'unresolved')

            os.environ['TEST_ARRAY'] = '[1, 2, 3]'
            test_array = c.test_array
            self.assertEqual(test_array, [1, 2, 3])

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class Arrays(DummyMemoryConfig):
            test_array = ArrayOption('TestArray', choices=[[1, 2, 3], [4, 5, 6]], env_name='TEST_ARRAY')

        c = Arrays.get_instance()
        os.environ['TEST_ARRAY'] = '[1]'

        with self.assertRaises(ValidationError):
            test_array = c.test_array

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_array = c.test_array
            self.assertEqual(test_array, 'unresolved')

            os.environ['TEST_ARRAY'] = '[4, 5, 6]'
            test_array = c.test_array
            self.assertEqual(test_array, [4, 5, 6])

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('TestArray', '["1", "2", 3]')

        c.test_array = ["1"]
        self.assertEqual(c.test_array, ["1"])

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.test_array = "super array"

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.test_array = [1]
        c.test_array = None
        self.assertEqual(c.test_array, ["1", "2", "3"])

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.test_array
        self.assertEqual(c.test_array, ["1", "2", "3"])

    def test_env_is_first_json_deserialized_then_deserialized(self):
        class Arrays(DummyMemoryConfig):
            test_array = ArrayOption('ArrayOption', env_name='TEST_ARRAY')

        os.environ['TEST_ARRAY'] = '[1]'
        c = Arrays.get_instance()

        with patch.object(ArrayOption, 'deserialize_json', return_value=[1]) as mock_deserialize_json:
            test_array = c.test_array

        with patch.object(ArrayOption, 'deserialize', return_value=[1]) as mock_deserialize:
            test_array = c.test_array

        mock_deserialize_json.assert_called_with('[1]')
        mock_deserialize.assert_called_with([1])

    def test_env_value_must_be_valid_json(self):
        os.environ['TEST_ARRAY'] = ']'

        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            test_array = c.test_array
#}
