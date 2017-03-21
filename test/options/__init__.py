from abc import ABC
from collections import namedtuple
from functools import partial
import os
from unittest.mock import patch
import uuid

from nativeconfig.exceptions import DeserializationError, ValidationError

from test import StubConfig


Option = namedtuple('OptionName', [
    'option_type',
    'value',
    'alternate_value',
    'invalid_value',
    'invalid_json_value',
    'invalid_raw_value'
])


def make_option_type(option_type, **kwargs):
    t = partial(option_type, **kwargs)
    t.__doc__ = option_type.__doc__
    return t


class TestOptionMixin(ABC):
    OPTIONS = None
    OPTION_ENV_NAME = str(uuid.uuid4())

    def tearDown(self):
        os.environ.pop(self.OPTION_ENV_NAME, None)

    def test_name_must_be_nonempty_string(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type(name=None)

            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type(name='')

            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type(name=42)

            class MyConfig(StubConfig):
                option = o.option_type(name='_')

    def test_env_name_must_be_nonempty_string_if_set(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', env_name='')

            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', env_name=42)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME)

    def test_choices_must_be_nonempty_iterable_if_set(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', choices=[])

            with self.assertRaises(ValueError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', choices=42)

            class MyConfig(StubConfig):
                option = o.option_type('_', choices=[o.value])

    def test_choices_deep_copied(self):
        for o in self.OPTIONS:
            choices = [o.value]

            class MyConfig(StubConfig):
                option = o.option_type('_', choices=choices)

            choices[0] = o.alternate_value

            self.assertEqual(MyConfig.option.choices, [o.value])

    def test_choices_property_returns_deep_copy(self):
        for o in self.OPTIONS:
            option = o.option_type('_', choices=[o.value, o.alternate_value])

            choices = option.choices
            self.assertEqual(choices, option._choices)

            choices.pop()
            self.assertNotEqual(choices, option._choices)
            self.assertEqual(choices, [o.value])
            self.assertEqual(option._choices, [o.value, o.alternate_value])

    def test_doc_passed_from_constructor(self):
        doc_string = 'Test option'

        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_', doc=doc_string)

            self.assertEqual(MyConfig.option.__doc__, doc_string)
            self.assertEqual(MyConfig.get_instance().option_for_name('_').__doc__, doc_string)

    def test_doc_inherited_if_not_passed(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            self.assertEqual(MyConfig.option.__doc__, o.option_type.__doc__)
            self.assertEqual(MyConfig.get_instance().option_for_name('_').__doc__, o.option_type.__doc__)

    def test_default_must_be_in_choices_if_set(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValidationError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', default=o.value, choices=[o.alternate_value])

            class MyConfig(StubConfig):
                option = o.option_type('_', default=o.value, choices=[o.value])

    def test_choices_must_be_valid_if_set(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValidationError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', choices=[o.invalid_value])

    def test_default_must_be_valid_if_set(self):
        for o in self.OPTIONS:
            with self.assertRaises(ValidationError):
                class MyConfig(StubConfig):
                    option = o.option_type('_', default=o.invalid_value)

    def test_serialized_value_can_be_deserialized(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            raw_value = MyConfig.option.serialize(o.value)
            python_value = MyConfig.option.deserialize(raw_value)
            self.assertEqual(python_value, o.value)

    def test_json_serialized_value_can_be_deserialized(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            json_value = MyConfig.option.serialize_json(o.value)
            python_value = MyConfig.option.deserialize_json(json_value)
            self.assertEqual(python_value, o.value)

    def test_deserialize_json_from_None(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            self.assertEqual(MyConfig.option.deserialize_json('null'), None)

    def test_setting_value(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            c = MyConfig.get_instance()

            c.option = o.value
            self.assertEqual(c.option, o.value)

            c.option = o.alternate_value
            self.assertEqual(c.option, o.alternate_value)

    def test_value_must_be_valid(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_')

            c = MyConfig.get_instance()

            c.option = o.value
            self.assertEqual(c.option, o.value)

            with self.assertRaises(ValidationError):
                c.option = o.invalid_value

    def test_None_is_always_invalid(self):
        for o in self.OPTIONS:
            option = o.option_type('_')

            with self.assertRaises(ValidationError):
                option.validate(None)

    def test_value_must_be_in_choices_if_set(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_', choices=[o.value])

            c = MyConfig.get_instance()

            with self.assertRaises(ValidationError):
                c.option = o.alternate_value

            with self.assertRaises(ValidationError):
                c.set_json_value_for_option_name('_', MyConfig.option.serialize_json(o.alternate_value))

            with self.assertRaises(ValidationError):
                c.set_raw_value_for_option_name('_', MyConfig.option.serialize(o.alternate_value))

    def test_setting_env_value(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME)

            c = MyConfig.get_instance()

            c.option = o.value
            self.assertEqual(c.option, o.value)

            os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.alternate_value)
            self.assertEqual(c.option, o.alternate_value)

    def test_env_value_must_be_valid(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME)

            c = MyConfig.get_instance()

            c.option = o.value
            self.assertEqual(c.option, o.value)

            os.environ[self.OPTION_ENV_NAME] = o.invalid_json_value
            with self.assertRaises(DeserializationError):
                c.option

    def test_env_value_must_be_in_choices_if_set(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME, choices=[o.value])

            c = MyConfig.get_instance()

            c.option = o.value
            self.assertEqual(c.option, o.value)

            os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.alternate_value)
            with self.assertRaises(ValidationError):
                c.option

    def test_deleting_value_resets_to_default(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_', default=o.value)

            c = MyConfig.get_instance()

            c.option = o.alternate_value
            self.assertEqual(c.option, o.alternate_value)

            c.option = None
            self.assertEqual(c.option, o.value)

            c.option = o.alternate_value
            self.assertEqual(c.option, o.alternate_value)

            del c.option
            self.assertEqual(c.option, o.value)

    def test_deleting_value_preserves_env_if_set(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME)

            c = MyConfig.get_instance()

            os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.value)
            self.assertEqual(c.option, o.value)

            del c.option
            self.assertEqual(c.option, o.value)

    def test_value_that_cannot_be_deserialized_calls_resolver(self):
        for o in self.OPTIONS:
            if o.invalid_raw_value is None:
                continue

            class MyConfig(StubConfig):
                option = o.option_type('_')

            c = MyConfig.get_instance()
            getattr(c, MyConfig.option._setter)('_', o.invalid_raw_value)

            with self.assertRaises(DeserializationError):
                c.option

            with patch.object(StubConfig, 'resolve_value', return_value='unresolved'):
                self.assertEqual(c.option, 'unresolved')

                getattr(c, MyConfig.option._setter)('_', MyConfig.option.serialize(o.value))
                self.assertEqual(c.option, o.value)

    def test_invalid_deserialized_value_calls_resolver(self):
        for o in self.OPTIONS:
            class MyConfig(StubConfig):
                option = o.option_type('_', choices=[o.value])

            c = MyConfig.get_instance()
            getattr(c, MyConfig.option._setter)('_', MyConfig.option.serialize(o.alternate_value))

            with self.assertRaises(ValidationError):
                c.option

            with patch.object(StubConfig, 'resolve_value', return_value='unresolved'):
                self.assertEqual(c.option, 'unresolved')

                getattr(c, MyConfig.option._setter)('_', MyConfig.option.serialize(o.value))
                self.assertEqual(c.option, o.value)

    def test_env_value_that_cannot_be_deserialized_calls_resolver(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME)

            c = MyConfig.get_instance()
            os.environ[self.OPTION_ENV_NAME] = o.invalid_json_value

            with self.assertRaises(DeserializationError):
                c.option

            with patch.object(StubConfig, 'resolve_value', return_value='unresolved'):
                self.assertEqual(c.option, 'unresolved')

                os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.value)
                self.assertEqual(c.option, o.value)

            os.environ[self.OPTION_ENV_NAME] = '['

            with self.assertRaises(DeserializationError):
                c.option

            with patch.object(StubConfig, 'resolve_value', return_value='unresolved'):
                self.assertEqual(c.option, 'unresolved')

                os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.value)
                self.assertEqual(c.option, o.value)

    def test_invalid_deserialized_env_value_calls_resolver(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME, choices=[o.value])

            c = MyConfig.get_instance()
            os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.alternate_value)

            with self.assertRaises(ValidationError):
                c.option

            with patch.object(StubConfig, 'resolve_value', return_value='unresolved'):
                self.assertEqual(c.option, 'unresolved')

                os.environ[self.OPTION_ENV_NAME] = MyConfig.option.serialize_json(o.value)
                self.assertEqual(c.option, o.value)

    def test_use_default_when_env_value_is_None(self):
        for o in self.OPTIONS:
            os.environ.pop(self.OPTION_ENV_NAME, None)

            class MyConfig(StubConfig):
                option = o.option_type('_', env_name=self.OPTION_ENV_NAME, default=o.value)

            c = MyConfig.get_instance()

            getattr(c, MyConfig.option._setter)('_', MyConfig.option.serialize(o.alternate_value))
            self.assertEqual(c.option, o.alternate_value)

            os.environ[self.OPTION_ENV_NAME] = 'null'
            self.assertEqual(c.option, o.value)
