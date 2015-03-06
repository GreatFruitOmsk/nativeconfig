from itertools import chain
import os
import unittest

from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError
from nativeconfig.options import FloatOption

from test import DummyMemoryConfig
from test import all_casings
from test.options import TestOptionMixin


class MyConfig(DummyMemoryConfig):
    height = FloatOption('Height', default=185.5)
    width = FloatOption('Width', env_name='WIDTH')


class TestFloatOption(unittest.TestCase, TestOptionMixin):
    @classmethod
    def setUpClass(cls):
        cls.OPTION_TYPE = FloatOption

    def tearDown(self):
        c = MyConfig.get_instance()
        del c.height
        del c.width
        os.unsetenv('WIDTH')

#{ Custom

    def test_cannot_be_empty(self):
        c = MyConfig.get_instance()

        c.set_value('Height', "")
        self.assertEqual(c.height, 185.5)


#{ TestOptionMixin

    def test_choices_cannot_be_empty(self):
        c = MyConfig.get_instance()
        with self.assertRaises(InitializationError):
            c.empty_choices = FloatOption('EmptyChoices', choices=[])

    def test_default_value_must_be_one_of_choices_if_any(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                float_value = self.OPTION_TYPE('Float', choices=[12.3, 45.6], default=42)

    def test_all_choices_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                some_float_value = self.OPTION_TYPE('Float', choices=[14.4, 27, '14.5', ''], default=27)

    def test_default_must_be_valid(self):
        with self.assertRaises(ValidationError):
            class MyConfig(DummyMemoryConfig):
                some_float_value = self.OPTION_TYPE('Float', default='1a')

    def test_value_must_be_one_of_choices_if_any(self):
        class MyConfig(DummyMemoryConfig):
            some_float = self.OPTION_TYPE('Float', choices=[12.3, 45.6])

        with self.assertRaises(ValidationError):
            MyConfig.get_instance().some_float = 42

        MyConfig.get_instance().some_float = 12.3
        MyConfig.get_instance().some_float = 45.6

    def test_serialize_json(self):
        c = MyConfig.get_instance()
        c.height = 0.1
        self.assertEqual(c.get_value_for_option_name('Height'), '0.1')

    def test_deserialize_json(self):
        c = MyConfig.get_instance()
        c.set_value_for_option_name('Height', '12.5')
        self.assertEqual(c.height, 12.5)

    def test_value_can_be_overridden_by_env(self):
        os.environ['WIDTH'] = '123.4'
        c = MyConfig.get_instance()
        self.assertEqual(c.width, 123.4)

    def test_value_can_be_overridden_by_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Height', '234.5')
        self.assertEqual(c.height, 234.5)

    def test_value_that_cannot_be_deserialized_during_get_calls_resolver(self):
        pass

    def test_invalid_deserialized_value_during_get_calls_resolver(self):
        pass

    def test_setting_value_resets_one_shot_value(self):
        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('Height', '234.5')
        self.assertEqual(c.height, 234.5)

        c.height = 345.6
        self.assertEqual(c.height, 345.6)

    def test_setting_invalid_value_raises_exception(self):
        c = MyConfig.get_instance()
        with self.assertRaises(ValidationError):
            c.height = "vysoko-vysoko"

    def test_setting_none_deletes_value(self):
        pass

    def test_deleting_value(self):
        pass

    def test_env_is_first_json_deserialized_then_deserialized(self):
        pass

#}
