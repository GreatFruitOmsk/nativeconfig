from itertools import chain
import unittest

from nativeconfig import BooleanOption

from test import StubConfig, all_casings
from test.options import TestOptionMixin, make_option_type, Option


class MyConfig(StubConfig):
    boolean_true = BooleanOption('BooleanTrue', env_name='BOOLEAN_TRUE', default=True)
    boolean_false = BooleanOption('BooleanFalse', default=False)


class TestBooleanOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=make_option_type(BooleanOption),
                value=True,
                alternate_value=False,
                invalid_value='42',
                invalid_json_value='1.0',
                invalid_raw_value='hello'
            ),
        ]

    def test_true_serialized_to_1(self):
        c = MyConfig.get_instance()
        c.boolean_false = True
        self.assertEqual(c.get_value('BooleanFalse'), '1')

    def test_false_serialized_to_0(self):
        c = MyConfig.get_instance()
        c.boolean_true = False
        self.assertEqual(c.get_value('BooleanTrue'), '0')

    def test_deserialization_of_allowed_true_values(self):
        c = MyConfig.get_instance()

        for v in chain.from_iterable([all_casings(v) for v in BooleanOption.TRUE_RAW_VALUES]):
            c.set_value('BooleanFalse', v)
            self.assertEqual(c.boolean_false, True)

    def test_deserialization_of_allowed_false_values(self):
        c = MyConfig.get_instance()

        for v in chain.from_iterable([all_casings(v) for v in BooleanOption.FALSE_RAW_VALUES]):
            c.set_value('BooleanTrue', v)
            self.assertEqual(c.boolean_true, False)
