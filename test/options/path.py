import os
from pathlib import Path
import unittest
from unittest.mock import patch

from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError
from nativeconfig.options.path import PathOption

from test import DummyMemoryConfig
from test import all_casings
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    my_path = PathOption('MyPath', env_name='MY_PATH', default=Path("."))


class TestPathOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = PathOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.my_path
        os.unsetenv('MY_PATH')

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = PathOption('EmptyChoices', choices=[], default=Path("."))

    def test_default_value_must_be_one_of_choices_if_any(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.invalid_default_choice = PathOption('InvalidDefaultChoice', choices=[Path("."), Path("/usr/bin")],
                                                  default=".")

    def test_all_choices_must_be_valid(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.invalid_choices = self.OPTION_TYPE('InvalidChoices', choices=[Path("."), Path("/usr/bin"), "."])

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                invalid_default = self.OPTION_TYPE('InvalidDefault', default="/usr/bin")

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            value_with_choices = self.OPTION_TYPE('ValueWithChoices', choices=[Path("."), Path("C:\\Windows")])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().value_with_choices = Path("/")

        MyConfig.get_instance().value_with_choices = Path(".")
        MyConfig.get_instance().value_with_choices = Path("C:\\Windows")

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.my_path = Path(".")
        self.assertEqual(c.get_value_for_option_name('MyPath'), '\".\"')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('MyPath', '\".\"')
        self.assertEqual(c.my_path, Path("."))

    def test_value_can_be_overridden_by_env(self):
        os.environ['MY_PATH'] = '\"/home/user\"'
        c = MyConfig.get_instance()
        self.assertEqual(c.my_path, Path('/home/user'))

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('MyPath', '\"/home/user\"')
        self.assertEqual(c.my_path, Path('/home/user'))

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        pass  # all valid unicode strings can be interpreted as Path

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        class Paths(DummyMemoryConfig):
            path = PathOption('Path', choices=[Path("/"), Path("/home/user")], env_name='PATH_OPTION', default=Path("/"))

        c = Paths.get_instance()
        os.environ['PATH_OPTION'] = '\"/home/hello\"'

        with self.assertRaises(ValidationError):
            my_path = c.path

        with patch.object(DummyMemoryConfig, 'resolve_value', return_value='unresolved'):
            my_path = c.path
            self.assertEqual(my_path, 'unresolved')

            os.environ['PATH_OPTION'] = '\"/home/user\"'
            my_path = c.path
            self.assertEqual(my_path, Path('/home/user'))

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('MyPath', '\"/home/user\"')

        c.my_path = Path('/home/none')
        self.assertEqual(c.my_path, Path('/home/none'))

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.my_path = "young"

    def test_setting_none_deletes_value(self):
        c = MyConfig.get_instance()
        c.my_path = Path("C:\\users\\User")
        c.my_path = None
        self.assertEqual(c.my_path, Path("."))

    def test_deleting_value(self):
        c = MyConfig.get_instance()
        del c.my_path
        self.assertEqual(c.my_path, Path("."))

    def test_env_is_first_json_deserialized_then_deserialized(self):
        class Paths(DummyMemoryConfig):
            path = PathOption('Path', choices=[Path("C:\\users\\User"), Path("/home/user")], env_name='TEST_PATH', default=Path("C:\\users\\User"))

        c = Paths.get_instance()
        os.environ['TEST_PATH'] = '\"/home/user\"'

        with patch.object(PathOption, 'deserialize_json', return_value='/home/user') as mock_deserialize_json:
            my_path = c.path

        with patch.object(PathOption, 'deserialize', return_value=Path('/home/user')) as mock_deserialize:
            my_path = c.path

        mock_deserialize_json.assert_called_with('\"/home/user\"')
        mock_deserialize.assert_called_with(Path('/home/user'))
