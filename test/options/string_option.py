import unittest

from nativeconfig import StringOption

from test.options import TestOptionMixin, Option, make_option_type


class TestStringOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=StringOption,
                value='hello',
                alternate_value='world',
                invalid_value=42,
                invalid_json_value='9000',
                invalid_raw_value=None
            ),
            Option(
                option_type=make_option_type(StringOption, allow_empty=False),
                value='hello',
                alternate_value='world',
                invalid_value='',
                invalid_json_value='9000',
                invalid_raw_value=None
            )
        ]
