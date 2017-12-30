import unittest

from nativeconfig.options import IntOption

from test.options import OptionMixin, Option


class TestIntOption(unittest.TestCase, OptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=IntOption,
                value=42,
                alternate_value=9000,
                invalid_value='hello',
                invalid_json_value='"world"',
                invalid_raw_value='hello world'
            )
        ]
