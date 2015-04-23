import os
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError
from nativeconfig.options import IntOption

from test import DummyMemoryConfig
from test import all_casings
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    fortytwo = IntOption('FortyTwo', env_name='FORTY_TWO', default=42)
    age = IntOption('Age', default=0)


class TestIntOption(unittest.TestCase, TestOptionMixin):

    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = IntOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.fortytwo
        del c.age
        try:
            del os.environ['FORTY_TWO']
        except KeyError:
            pass


    def test_json_serialization_deserialization(self):
        c = MyConfig.get_instance()

        self.assertEqual(c.get_value_for_option_name('FortyTwo'), '42')
        self.assertEqual(c.get_value_for_option_name('Age'), '0')

        c.set_value_for_option_name('FortyTwo', '45')
        self.assertEqual(c.fortytwo, 45)

        c.set_value_for_option_name('Age', '21')
        self.assertEqual(c.age, 21)


    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = IntOption('EmptyChoices', choices=[], default=1)

    def test_default_value_must_be_one_of_choices_if_any(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.lamp_cap_diameter = IntOption('LampCapDiameter', choices=[14, 27], default=42)

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                lamp_cap_diameter = self.OPTION_TYPE('Int', choices=[14, 27, 'e14', 'e27'], default=42)

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                int_value = self.OPTION_TYPE('Int', default="a")

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            lamp_cap_diameter = self.OPTION_TYPE('Int', choices=[14, 27], default=27)

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().lamp_cap_diameter = 28

        MyConfig.get_instance().lamp_cap_diameter = 14
        MyConfig.get_instance().lamp_cap_diameter = 27

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.fortytwo = 43
        self.assertEqual(c.get_value_for_option_name('FortyTwo'), '43')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('FortyTwo', '41')
        self.assertEqual(c.fortytwo, 41)

    def test_value_can_be_overridden_by_env(self):
        os.environ['FORTY_TWO'] = '39'
        c = MyConfig.get_instance()
        self.assertEqual(c.fortytwo, 39)

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Age', '21')
        self.assertEqual(c.age, 21)

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        c = MyConfig.get_instance()
        os.environ['FORTY_TWO'] = '\"FORTYTWO\"'

        with self.assertRaises(DeserializationError):
            fortytwo = c.fortytwo

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            fortytwo = c.fortytwo
            self.assertEqual(fortytwo, 'unresolved')

            os.environ['FORTY_TWO'] = '\"42\"'
            fortytwo = c.fortytwo
            self.assertEqual(fortytwo, 42)

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class Diameters(DummyMemoryConfig):
            lamp_cap_diameter = IntOption('LampCapDiameter', choices=[14, 27], env_name='LAMP_CAP_DIAMETER', default=27)

        c = Diameters.get_instance()
        os.environ['LAMP_CAP_DIAMETER'] = '\"9\"'

        with self.assertRaises(ValidationError):
            diameter = c.lamp_cap_diameter

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            diameter = c.lamp_cap_diameter
            self.assertEqual(diameter, 'unresolved')

            os.environ['LAMP_CAP_DIAMETER'] = '\"14\"'
            diameter = c.lamp_cap_diameter
            self.assertEqual(diameter, 14)

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('FortyTwo', '44')

        c.fortytwo = 43
        self.assertEqual(c.fortytwo, 43)

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.age = "young"

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.fortytwo = 44
        c.fortytwo = None
        self.assertEqual(c.fortytwo, 42)

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.fortytwo
        self.assertEqual(c.fortytwo, 42)

    def test_env_is_first_json_deserialized_then_deserialized(self):
        class Diameters(DummyMemoryConfig):
            lamp_cap_diameter = IntOption('LampCapDiameter', choices=[14, 27], env_name='LAMP_CAP_DIAMETER', default=27)

        c = Diameters.get_instance()
        os.environ['LAMP_CAP_DIAMETER'] = '\"14\"'

        with patch.object(IntOption, 'deserialize_json', return_value='14') as mock_deserialize_json:
            diameter = c.lamp_cap_diameter

        with patch.object(IntOption, 'deserialize', return_value=14) as mock_deserialize:
            diameter = c.lamp_cap_diameter

        mock_deserialize_json.assert_called_with('\"14\"')
        mock_deserialize.assert_called_with('14')
