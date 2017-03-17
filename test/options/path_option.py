from pathlib import Path, PurePosixPath
import unittest

from nativeconfig import PathOption

from test.options import TestOptionMixin, Option, make_option_type


class TestPathOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=PathOption,
                value=Path('/a'),
                alternate_value=Path('/b'),
                invalid_value=42,
                invalid_json_value='true',
                invalid_raw_value=None
            ),
            Option(
                option_type=make_option_type(PathOption, path_type=PurePosixPath),
                value=PurePosixPath('/a'),
                alternate_value=PurePosixPath('b'),
                invalid_value=42,
                invalid_json_value='42',
                invalid_raw_value=None
            )
        ]

    def test_path_type_must_be_an_instance_of_PurePath(self):
        with self.assertRaises(ValueError):
            PathOption('_', path_type=str)
