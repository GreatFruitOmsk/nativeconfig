import unittest

from nativeconfig.options import IntOption

from test.options import TestOptionMixin, Option


class TestIntOption(unittest.TestCase, TestOptionMixin):
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
