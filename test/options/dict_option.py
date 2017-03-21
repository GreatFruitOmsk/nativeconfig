import unittest

from nativeconfig import ArrayOption, DictOption, FloatOption, IntOption, StringOption

from test.options import TestOptionMixin, Option, make_option_type


class TestDictOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=make_option_type(DictOption, value_type=IntOption('_')),
                value={'key1': 42},
                alternate_value={'key2': 9000},
                invalid_value={'key2': 'hello'},
                invalid_json_value='{"key2": "world"}',
                invalid_raw_value={'key2': 'hello'}
            ),
            Option(
                option_type=make_option_type(DictOption, value_type=FloatOption('_')),
                value={'key1': 1.0},
                alternate_value={'key2': 2.0},
                invalid_value={'key2': 'hello'},
                invalid_json_value='"world"',
                invalid_raw_value={'key2': 'hello'}
            ),
            Option(
                option_type=make_option_type(DictOption, value_type=FloatOption('_')),
                value={'key1': 1.0},
                alternate_value={'key2': 2.0},
                invalid_value='hello',
                invalid_json_value='"world"',
                invalid_raw_value={'key2': 'hello'}
            ),
        ]

    def test_value_type_must_be_instance_of_base_option(self):
        with self.assertRaises(ValueError):
            DictOption('_', value_type=str)

        DictOption('_', value_type=StringOption('_'))

    def test_value_type_cannot_be_container(self):
        with self.assertRaises(ValueError):
            DictOption('_', value_type=ArrayOption('_', value_type=StringOption('_')))
