import os
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, ValidationError, DeserializationError
from nativeconfig.options import FloatOption

from test import DummyMemoryConfig
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    height = FloatOption('Height', default=185.5)
    width = FloatOption('Width', env_name='WIDTH')


class TestFloatOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = FloatOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.height
        del c.width
        try:
            del os.environ['WIDTH']
        except KeyError:
            pass


#{ Custom

    def test_cannot_be_empty(self):
        c = MyConfig.get_instance()

        c.set_value('Height', "")
        self.assertEqual(c.height, 185.5)


#{ TestOptionMixin

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = FloatOption('EmptyChoices', choices=[])

    def test_default_value_must_be_one_of_choices_if_any(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                float_value = self.OPTION_TYPE('Float', choices=[12.3, 45.6], default=42)

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                some_float_value = self.OPTION_TYPE('Float', choices=[14.4, 27, '14.5', ''], default=27)

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                some_float_value = self.OPTION_TYPE('Float', default='1a')

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            some_float = self.OPTION_TYPE('Float', choices=[12.3, 45.6])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().some_float = 42

        MyConfig.get_instance().some_float = 12.3
        MyConfig.get_instance().some_float = 45.6

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.height = 0.1
        self.assertEqual(c.get_value_for_option_name('Height'), '0.1')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('Height', '12.5')
        self.assertEqual(c.height, 12.5)

    def test_value_can_be_overridden_by_env(self):
        os.environ['WIDTH'] = '123.4'
        c = MyConfig.get_instance()
        self.assertEqual(c.width, 123.4)

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Height', '234.5')
        self.assertEqual(c.height, 234.5)

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['WIDTH'] = '\"FORTYTWO\"'

        with self.assertRaises(DeserializationError):
            width = c.width

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            width = c.width
            self.assertEqual(width, 'unresolved')

            os.environ['WIDTH'] = '\"4.2\"'
            width = c.width
            self.assertEqual(width, 4.2)

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class Diameters(DummyMemoryConfig):
            hdd_diameter = FloatOption('HddDiameter', choices=[2.5, 3.5], env_name='HDD_DIAMETER', default=3.5)

        c = Diameters.get_instance()
        os.environ['HDD_DIAMETER'] = '\"5.0\"'

        with self.assertRaises(ValidationError):
            diameter = c.hdd_diameter

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            diameter = c.hdd_diameter
            self.assertEqual(diameter, 'unresolved')

            os.environ['HDD_DIAMETER'] = '\"3.5\"'
            diameter = c.hdd_diameter
            self.assertEqual(diameter, 3.5)

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Height', '234.5')

        c.height = 345.6
        self.assertEqual(c.height, 345.6)

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.height = "very_high"

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.height = 1.0
        c.height = None
        self.assertEqual(c.height, 185.5)

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.height
        self.assertEqual(c.height, 185.5)

    def test_env_is_first_json_deserialized_then_deserialized(self):
        c = MyConfig.get_instance()
        os.environ['WIDTH'] = '\"4.2\"'
        with patch.object(FloatOption, 'deserialize_json', return_value='4.2') as mock_deserialize_json:
            w = c.width

        with patch.object(FloatOption, 'deserialize', return_value=4.2) as mock_deserialize:
            w = c.width

        mock_deserialize_json.assert_called_with('\"4.2\"')
        mock_deserialize.assert_called_with('4.2')

    def test_env_value_must_be_valid_json(self):
        os.environ['WIDTH'] = "]"
        with self.assertRaises(DeserializationError):
            c = MyConfig.get_instance()
            width = c.width

#}
