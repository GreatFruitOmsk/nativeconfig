import unittest

from nativeconfig import DeserializationError
from nativeconfig import ArrayOption, FloatOption, IntOption, StringOption

from test.options import TestOptionMixin, Option, make_option_type


class TestArrayOption(TestOptionMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=make_option_type(ArrayOption, value_type=IntOption('_')),
                value=[42],
                alternate_value=[9000],
                invalid_value=['hello'],
                invalid_json_value='["world"]',
                invalid_raw_value=['hello'],
            ),
            Option(
                option_type=make_option_type(ArrayOption, value_type=FloatOption('_')),
                value=[1.0],
                alternate_value=[2.0],
                invalid_value='hello',
                invalid_json_value='["world"]',
                invalid_raw_value=['hello'],
            )
        ]

    def test_value_type_must_be_instance_of_base_option(self):
        with self.assertRaises(ValueError):
            ArrayOption('_', value_type=str)

        ArrayOption('_', value_type=StringOption('_'))

    def test_value_type_cannot_be_container(self):
        with self.assertRaises(ValueError):
            ArrayOption('_', value_type=ArrayOption('_', value_type=StringOption('_')))

    def test_json_value_must_be_list(self):
        with self.assertRaises(DeserializationError):
            ArrayOption('_', value_type=FloatOption('_')).deserialize_json('42')
