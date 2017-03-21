import os
from enum import Enum
from pathlib import Path
import unittest

from nativeconfig import EnumOption, PathOption, IntOption, FloatOption, StringOption, ArrayOption

from test import StubConfig
from test.options import TestOptionMixin, Option, make_option_type


class IntEnum(int, Enum):
    A = 1
    B = 2


class FloatEnum(float, Enum):
    A = 1.0
    B = 2.0


class StringEnum(str, Enum):
    A = 'a'
    B = 'b'


class PathEnum(Enum):
    A = Path('/a')
    B = Path('/b')


class TestEnumOption(TestOptionMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.OPTIONS = [
            Option(
                option_type=make_option_type(EnumOption, enum_type=IntEnum),
                value=IntEnum.A,
                alternate_value=IntEnum.B,
                invalid_value=FloatEnum.A,
                invalid_json_value='"string"',
                invalid_raw_value='string'
            ),
            Option(
                option_type=make_option_type(EnumOption, enum_type=FloatEnum),
                value=FloatEnum.A,
                alternate_value=FloatEnum.B,
                invalid_value='string',
                invalid_json_value='"string"',
                invalid_raw_value='string'
            ),
            Option(
                option_type=make_option_type(EnumOption, enum_type=StringEnum),
                value=StringEnum.A,
                alternate_value=StringEnum.B,
                invalid_value=IntEnum.A,
                invalid_json_value='42',
                invalid_raw_value=None
            ),
            Option(
                option_type=make_option_type(EnumOption, enum_type=PathEnum, value_type=PathOption('_')),
                value=PathEnum.A,
                alternate_value=PathEnum.B,
                invalid_value=IntEnum.A,
                invalid_json_value='42',
                invalid_raw_value=None
            ),
            Option(
                option_type=make_option_type(EnumOption, enum_type=PathEnum),
                value=PathEnum.A,
                alternate_value=PathEnum.B,
                invalid_value=IntEnum.A,
                invalid_json_value='42',
                invalid_raw_value=None
            )
        ]

    def test_value_type_is_set_for_known_types(self):
        class MyConfig(StubConfig):
            int_enum = EnumOption('IntEnum', IntEnum, env_name='TEST_ENUM', default=IntEnum.B)
            float_enum = EnumOption('FloatEnum', FloatEnum)
            str_enum = EnumOption('StringEnum', StringEnum)
            path_enum = EnumOption('PathEnum', PathEnum, value_type=PathOption('_'))
            path_enum_no_value_type = EnumOption('PathEnum2', PathEnum)

        self.assertIsInstance(MyConfig.int_enum._value_type, IntOption)
        self.assertIsInstance(MyConfig.float_enum._value_type, FloatOption)
        self.assertIsInstance(MyConfig.str_enum._value_type, StringOption)
        self.assertIsNone(MyConfig.path_enum_no_value_type._value_type)

    def test_enum_type_must_subclass_Enum(self):
        with self.assertRaises(ValueError):
            class MyConfig(StubConfig):
                enum_option = EnumOption('_', int)

    def test_value_type_cannot_be_container(self):
        with self.assertRaises(ValueError):
            class MyConfig(StubConfig):
                enum_option = EnumOption('_', IntEnum, value_type=ArrayOption('_', value_type=StringOption('_')))

    def test_can_deserialize_from_enum_name(self):
        class MyConfig(StubConfig):
            enum_option = EnumOption('_', IntEnum, env_name=self.OPTION_ENV_NAME)

        c = MyConfig.get_instance()

        self.assertIsNone(c.enum_option)

        c.set_value('_', 'A')
        self.assertEqual(c.enum_option, IntEnum.A)

        del c.enum_option
        self.assertIsNone(c.enum_option)

        os.environ[self.OPTION_ENV_NAME] = '"A"'
        self.assertEqual(c.enum_option, IntEnum.A)
