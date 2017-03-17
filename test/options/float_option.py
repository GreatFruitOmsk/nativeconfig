import unittest

from nativeconfig import FloatOption

from test.options import TestOptionMixin, Option


class TestFloatOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=FloatOption,
                value=42.0,
                alternate_value=9000.0,
                invalid_value='hello',
                invalid_json_value='true',
                invalid_raw_value='world'
            )
        ]
