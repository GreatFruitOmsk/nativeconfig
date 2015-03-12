import os
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options.array import ArrayOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    test_array = ArrayOption('TestArray', env_name='TEST_ARRAY', default=["1", "2", "3"])


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
        c.test_array = [1, 2, 3]
        self.assertEqual(c.get_value_for_option_name('TestArray'), '[1, 2, 3]')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('TestArray', '[1, "2", 3]')
        self.assertEqual(c.test_array, [1, "2", 3])

    def test_value_can_be_overridden_by_env(self):
        os.environ['TEST_ARRAY'] = '[1, 2, "3"]'
        c = MyConfig.get_instance()
        self.assertEqual(c.test_array, [1, 2, "3"])

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('TestArray', '[1]')
        self.assertEqual(c.test_array, [1])

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['TEST_ARRAY'] = '1'

        with self.assertRaises(DeserializationError):
            test_array = c.test_array

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            test_array = c.test_array
            self.assertEqual(test_array, 'unresolved')

            os.environ['TEST_ARRAY'] = '[1, 2]'
            test_array = c.test_array
            self.assertEqual(test_array, [1, 2])

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        pass
        # class Diameters(DummyMemoryConfig):
        #     hdd_diameter = FloatOption('HddDiameter', choices=[2.5, 3.5], env_name='HDD_DIAMETER', default=3.5)
        #
        # c = Diameters.get_instance()
        # os.environ['HDD_DIAMETER'] = '\"5.0\"'
        #
        # with self.assertRaises(ValidationError):
        #     diameter = c.hdd_diameter
        #
        # with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
        #     diameter = c.hdd_diameter
        #     self.assertEqual(diameter, 'unresolved')
        #
        #     os.environ['HDD_DIAMETER'] = '\"3.5\"'
        #     diameter = c.hdd_diameter
        #     self.assertEqual(diameter, 3.5)

    def test_setting_value_resets_one_shot_value(self):
        pass
        # c = MyConfig.get_instance()
        # c.set_one_shot_value_for_option_name('Height', '234.5')
        #
        # c.height = 345.6
        # self.assertEqual(c.height, 345.6)

    def test_setting_invalid_value_raises_exception(self):
        pass
        # c = MyConfig.get_instance()
        # with self.assertRaises(ValidationError):
        #     c.height = "very_high"

    def test_setting_none_deletes_value(self):
        pass
        # c = MyConfig.get_instance()
        # c.height = 1.0
        # c.height = None
        # self.assertEqual(c.height, 185.5)

    def test_deleting_value(self):
        pass
        # c = MyConfig.get_instance()
        # del c.height
        # self.assertEqual(c.height, 185.5)

    def test_env_is_first_json_deserialized_then_deserialized(self):
        pass
        # c = MyConfig.get_instance()
        # os.environ['WIDTH'] = '\"4.2\"'
        # with patch.object(FloatOption, 'deserialize_json', return_value='4.2') as mock_deserialize_json:
        #     w = c.width
        #
        # with patch.object(FloatOption, 'deserialize', return_value=4.2) as mock_deserialize:
        #     w = c.width
        #
        # mock_deserialize_json.assert_called_with('\"4.2\"')
        # mock_deserialize.assert_called_with('4.2')

#}
