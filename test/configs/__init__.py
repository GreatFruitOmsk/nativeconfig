from abc import ABC, abstractmethod
import json
import os
from unittest.mock import MagicMock

from nativeconfig.options import StringOption, IntOption, ArrayOption, DictOption, ValueSource
from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError


class TestConfigMixin(ABC):
    CONFIG_TYPE = None

    def tearDown(self):
        os.environ.pop('FIRST_NAME', None)

    def test_exception_is_raised_for_duplicate_options(self):
        with self.assertRaises(AttributeError):
            class MyConfig(self.CONFIG_TYPE):
                first_name = StringOption('Name')
                last_name = StringOption('Name')
            MyConfig.get_instance()

    def test_default_values_are_not_written_to_config(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        MyConfig.get_instance().del_value_for_option_name('FirstName')
        self.assertEqual(MyConfig.get_instance().get_value('FirstName'), None)

    def test_get_value_for_option_name_returns_python(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(c.get_value_for_option_name('FirstName'), 'Ilya')

    def test_get_raw_value_for_option_name_returns_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(c.option_for_name('FirstName').deserialize(c.get_raw_value_for_option_name('FirstName')), 'Ilya')

    def test_get_json_value_for_option_name_returns_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(json.loads(c.get_json_value_for_option_name('FirstName')), 'Ilya')

    def test_get_value_for_option_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            self.assertEqual(c.get_value_for_option_name('LastName'), None)

    def test_get_raw_value_for_option_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.get_raw_value_for_option_name('LastName')

    def test_get_json_value_for_option_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.get_json_value_for_option_name('LastName')

    def test_set_value_for_option_name_accepts_python(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.set_value_for_option_name('FirstName', 'Artem')
        self.assertEqual(c.first_name, 'Artem')

    def test_set_raw_value_for_option_name_accepts_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        c.set_raw_value_for_option_name('Age', c.option_for_name('Age').serialize(9000))
        self.assertEqual(c.age, 9000)

        with self.assertRaises(DeserializationError):
            c.set_raw_value_for_option_name('Age', 'Artem')

    def test_set_json_value_for_option_name_accepts_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.set_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Artem')

        with self.assertRaises(DeserializationError):
            c.set_json_value_for_option_name('FirstName', 'Artem')

    def test_set_None_value_for_option_name_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        self.assertEqual(c.get_value_for_option_name('FirstName'), 'Artem')
        c.set_value_for_option_name('FirstName', None)
        self.assertEqual(c.get_value('FirstName'), None)

    def test_set_null_json_value_for_option_name_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        self.assertEqual(c.get_json_value_for_option_name('FirstName'), '"Artem"')
        c.set_json_value_for_option_name('FirstName', json.dumps(None))
        self.assertEqual(c.get_value('FirstName'), None)

    def test_set_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_value_for_option_name('LastName', 'Kulakov')

    def test_set_raw_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_json_value_for_option_name('LastName', 'Kulakov')

    def test_set_json_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_json_value_for_option_name('LastName', '"Kulakov"')

    def test_set_one_shot_value_for_option_name_accepts_python(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        c.set_one_shot_value_for_option_name('Age', 9000)
        self.assertEqual(c.age, 9000)

        with self.assertRaises(ValidationError):
            c.set_one_shot_value_for_option_name('Age', '9000')

    def test_set_one_shot_raw_value_for_option_name_accepts_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        c.set_one_shot_raw_value_for_option_name('Age', c.option_for_name('Age').serialize(9000))
        self.assertEqual(c.age, 9000)

        with self.assertRaises(DeserializationError):
            c.set_one_shot_raw_value_for_option_name('Age', 'fortytwo')

    def test_set_one_shot_json_value_for_option_name_accepts_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Artem')

        with self.assertRaises(DeserializationError):
            c.set_one_shot_json_value_for_option_name('FirstName', 'Artem')

    def test_set_one_shot_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_one_shot_value_for_option_name('LastName', 'Kulakov')

    def test_set_one_shot_raw_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_one_shot_raw_value_for_option_name('LastName', c.option_for_name('FirstName').serialize('Kulakov'))

    def test_set_one_shot_json_value_for_option_name_raises_key_error_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.set_one_shot_json_value_for_option_name('LastName', '"Kulakov"')

    def test_one_shot_value_overrides_config(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_value_for_option_name('FirstName', 'Artem')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

        c.set_one_shot_value_for_option_name('FirstName', 'Ivan')
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)

    def test_one_shot_raw_value_overrides_config(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

        c.set_one_shot_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Ivan'))
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)

    def test_one_shot_json_value_overrides_config(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps('Ivan'))
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)

    def test_one_shot_value_does_not_override_env(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', env_name='FIRST_NAME')

        c = MyConfig.get_instance()
        os.environ['FIRST_NAME'] = json.dumps('Ivan')
        c.set_one_shot_value_for_option_name('FirstName', 'Artem')
        self.assertEqual(c.first_name, 'Ivan')

    def test_one_shot_raw_value_does_not_override_env(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', env_name='FIRST_NAME')

        c = MyConfig.get_instance()
        os.environ['FIRST_NAME'] = json.dumps('Ivan')
        c.set_one_shot_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Artem'))
        self.assertEqual(c.first_name, 'Ivan')

    def test_one_shot_json_value_does_not_override_env(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', env_name='FIRST_NAME')

        c = MyConfig.get_instance()
        os.environ['FIRST_NAME'] = json.dumps('Ivan')
        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Ivan')

    def test_one_shot_value_reset_by_set(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('FirstName', 'Artem')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        c.first_name = 'Ivan'
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_raw_value_reset_by_set(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        c.first_name = 'Ivan'
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_json_value_reset_by_set(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        c.first_name = 'Ivan'
        self.assertEqual(c.first_name, 'Ivan')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_value_reset_by_del(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('FirstName', 'Artem')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        del c.first_name
        self.assertEqual(c.first_name, 'Ilya')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_raw_value_reset_by_del(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        del c.first_name
        self.assertEqual(c.first_name, 'Ilya')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_json_value_reset_by_del(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, True)
        self.assertEqual(c.first_name, 'Artem')
        del c.first_name
        self.assertEqual(c.first_name, 'Ilya')
        self.assertEqual(c.option_for_name('FirstName')._is_one_shot_value_set, False)

    def test_one_shot_value_set_to_None_forces_default(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')
        c.set_one_shot_value_for_option_name('FirstName', None)
        self.assertEqual(c.first_name, 'Ilya')

    def test_one_shot_json_value_set_to_null_forces_default(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        self.assertEqual(c.first_name, 'Artem')
        c.set_one_shot_json_value_for_option_name('FirstName', json.dumps(None))
        self.assertEqual(c.first_name, 'Ilya')

    def test_del_value_for_option_name_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Ivan'
        c.del_value_for_option_name('FirstName')
        self.assertEqual(c.get_value('FirstName'), None)

    def test_del_value_for_option_name_raises_warn_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(KeyError):
            c.del_value_for_option_name('LastName')

    def test_validate_value_for_option_name_accepts_python(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.validate_value_for_option_name('FirstName', 'Artem')

    def test_validate_raw_value_for_option_name_accepts_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.validate_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Artem'))

    def test_validate_json_value_for_option_name_accepts_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.validate_json_value_for_option_name('FirstName', json.dumps('Artem'))

    def test_validate_value_for_option_name_raises_validation_error_for_invalid_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertRaises(ValidationError):
            c.validate_value_for_option_name('FirstName', 42)

    def test_validate_raw_value_for_option_name_raises_validation_error_for_invalid_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', choices=['Ilya', 'Artem'])

        c = MyConfig.get_instance()

        with self.assertRaises(ValidationError):
            c.validate_raw_value_for_option_name('FirstName', c.option_for_name('FirstName').serialize('Ivan'))

    def test_validate_json_value_for_option_name_raises_validation_error_for_invalid_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', choices=['Ilya', 'Artem'])

        c = MyConfig.get_instance()

        with self.assertRaises(ValidationError):
            c.validate_json_value_for_option_name('FirstName', json.dumps('Ivan'))

    def test_validate_raw_value_for_option_name_raises_deserialization_error_for_malformed_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        with self.assertRaises(DeserializationError):
            c.validate_raw_value_for_option_name('Age', 'fortytwo')

    def test_validate_json_value_for_option_name_raises_deserialization_error_for_malformed_json(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        with self.assertRaises(DeserializationError):
            c.validate_json_value_for_option_name('Age', '"fortytwo"')

    def test_items_enumerates_values(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        for option_name, (python_value, value_source) in c.python_items():
            if option_name == 'Age2':
                self.assertEqual((option_name, (python_value, value_source)), ('Age2', (42, ValueSource.default)))

    def test_raw_items_enumerates_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        for option_name, (raw_value, value_source) in c.raw_items():
            if option_name == 'Age2':
                self.assertEqual((option_name, (raw_value, value_source)), ('Age2', ('42', ValueSource.default)))

    def test_json_items_enumerates_raw(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig.get_instance()

        for option_name, (json_value, value_source) in c.json_items():
            if option_name == 'Age2':
                self.assertEqual((option_name, (json_value, value_source)), ('Age2', ('42', ValueSource.default)))

    def test_snapshot_returns_json_dict(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')
            last_name = StringOption('LastName', default='Kulakov')

        c = MyConfig.get_instance()
        s = c.snapshot()
        self.assertIsInstance(json.loads(s), dict)

    def test_option_for_name_returns_property(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(c.option_for_name('FirstName'), getattr(MyConfig, 'first_name'))

    def test_option_for_name_returns_None_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(c.option_for_name('LastName'), None)

    def test_resolve_value_is_called_to_resolve_broken_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.resolve_value = MagicMock()
        c.set_value('LuckyNumber', 'NotANumber')
        c.lucky_number
        self.assertEqual(c.resolve_value.call_count, 1)
        self.assertIsInstance(c.resolve_value.call_args[0][0][1], DeserializationError)
        self.assertEqual(c.resolve_value.call_args[0][1], 'LuckyNumber')
        self.assertEqual(c.resolve_value.call_args[0][2], 'NotANumber')

    def test_get_value_returns_raw_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.lucky_number = 1
        self.assertEqual(c.get_value('LuckyNumber'), '1')

    def test_get_value_returns_None_if_option_does_not_exist(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.lucky_number = 1
        self.assertEqual(c.get_value('UnluckyNumber'), None)

    def test_set_value_accepts_raw_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.set_value('LuckyNumber', '2')
        self.assertEqual(c.lucky_number, 2)

    def test_set_None_value_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.lucky_number = 10
        self.assertEqual(c.get_value('LuckyNumber'), '10')
        c.set_value('LuckyNumber', None)
        self.assertEqual(c.get_value('LuckyNumber'), None)

    def test_del_value_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber')

        c = MyConfig.get_instance()
        c.lucky_number = 1
        c.del_value('LuckyNumber')
        self.assertEqual(c.get_value('LuckyNumber'), None)

    def test_get_array_value_returns_list(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.lucky_numbers = [7, 42]
        self.assertIsInstance(c.get_array_value('LuckyNumber'), list)

    def test_get_array_value_returns_None_if_option_does_not_exist(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        self.assertEqual(c.get_array_value('FirstName'), None)

    def test_set_array_value_accepts_iterable(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.set_array_value('LuckyNumber', ['7', '42'])
        self.assertEqual(c.lucky_numbers, [7, 42])

        c.set_array_value('LuckyNumber', ('7', '42'))
        self.assertEqual(c.lucky_numbers, [7, 42])

    def test_set_None_array_value_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.lucky_numbers = [7, 42]
        self.assertEqual(c.lucky_numbers, [7, 42])
        c.set_array_value('LuckyNumber', None)
        self.assertEqual(c.lucky_numbers, None)

    def test_get_dict_value_returns_dict(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.lucky_numbers = {'a': 1}
        self.assertIsInstance(c.get_dict_value('LuckyNumber'), dict)

    def test_remove_fields_from_dict(self):
        class MyConfig(self.CONFIG_TYPE):
            test_dict = DictOption('TestDict')

        c = MyConfig.get_instance()

        c.test_dict = {"key1": "value1", "key2": "value2"}
        c.test_dict = {"key2": "value2"}
        self.assertEqual(c.test_dict, {"key2": "value2"})

    def test_get_dict_value_returns_None_if_option_does_not_exist(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()
        self.assertEqual(c.get_dict_value('FirstName'), None)

    def test_set_dict_value_accepts_dict(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.set_dict_value('LuckyNumber', {'a': '1'})
        self.assertEqual(c.lucky_numbers, {'a': 1})

    def test_set_None_dict_value_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'))

        c = MyConfig.get_instance()

        c.set_dict_value('LuckyNumber', {'a': '1'})
        self.assertEqual(c.lucky_numbers, {'a': 1})

        c.set_dict_value('LuckyNumber', None)
        self.assertEqual(c.lucky_numbers, None)

    def test_default_value_is_used_when_no_value_in_config(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber', default=42)

        c = MyConfig.get_instance()
        c.del_value_for_option_name('LuckyNumber')
        self.assertEqual(c.lucky_number, 42)

    def test_overriding_base_option_moves_it_to_the_end(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber', default=42)
            first_name = StringOption('FirstName')
            last_name = StringOption('LastName')

        class SubMyConfig(MyConfig):
            lucky_number = IntOption('LuckyNumber', default=9000)

        old_index = 0
        for i, option in enumerate(MyConfig._ordered_options):
            if option._name == 'LuckyNumber':
                old_index = i
                break

        new_index = 0
        for i, option in enumerate(SubMyConfig._ordered_options):
            if option._name == 'LuckyNumber':
                new_index = i
                break

        self.assertNotEqual(old_index, new_index)

    def test_custom_properties_are_allowed(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber', default=42)

            @property
            def custom_property(self):
                return '9000'

        c = MyConfig.get_instance()

    def test_ordered_options_supports_multiple_inheritance(self):
        class MyConfigMixin1:
            first_name = StringOption('FirstName', default='Ilya')

        class MyConfigMixin2:
            last_name = StringOption('LastName', default='Kulakov')

        class MyConfig(self.CONFIG_TYPE, MyConfigMixin1, MyConfigMixin2):
            age = IntOption('Age', default=42)

        self.assertIn(MyConfigMixin1.first_name._name, [o._name for o in MyConfig._ordered_options])
        self.assertIn(MyConfigMixin2.last_name, MyConfig._ordered_options)
        self.assertIn(MyConfig.age, MyConfig._ordered_options)

    def test_overriding_option_type_raises_warn_if_not_subclass(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        with self.assertWarns(UserWarning):
            class MyConfig2(MyConfig):
                first_name = IntOption('FirstName', default=42)

    def test_reset_deletes_from_config(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_number = IntOption('LuckyNumber', default=42)

        c = MyConfig.get_instance()

        c.lucky_number = 9000

        self.assertEqual(c.get_value('LuckyNumber'), '9000')
        c.reset()
        self.assertEqual(c.get_value('LuckyNumber'), None)

    def test_get_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=True)

        c = MyConfig.get_instance()
        c.get_value_cache_free = MagicMock(return_value='Ilya')

        c.first_name
        c.first_name
        c.first_name
        self.assertLessEqual(c.get_value_cache_free.call_count, 1)

    def test_set_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=True)

        c = MyConfig.get_instance()
        c.set_value_cache_free = MagicMock(return_value='Ilya')

        c.first_name = 'Ilya'
        c.first_name = 'Ilya'
        c.first_name = 'Ilya'
        self.assertLessEqual(c.set_value_cache_free.call_count, 1)

    def test_get_array_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'), default=(1, 2, 3), allow_cache=True)

        c = MyConfig.get_instance()
        c.get_array_value_cache_free = MagicMock(return_value=[1, 2, 3])
        c.lucky_numbers
        c.lucky_numbers
        c.lucky_numbers
        self.assertLessEqual(c.get_array_value_cache_free.call_count, 1)

    def test_set_array_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'), default=(1, 2, 3), allow_cache=True)

        c = MyConfig.get_instance()
        c.set_array_value_cache_free = MagicMock(return_value=[1, 2, 3])
        c.lucky_numbers = [1, 2, 3]
        c.lucky_numbers = [1, 2, 3]
        c.lucky_numbers = [1, 2, 3]
        self.assertLessEqual(c.set_array_value_cache_free.call_count, 1)

    def test_get_dict_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'), default={'a': 1, 'b': 2, 'c': 3}, allow_cache=True)

        c = MyConfig.get_instance()
        c.get_dict_value_cache_free = MagicMock(return_value={'a': 1, 'b': 2, 'c': 3})
        c.lucky_numbers
        c.lucky_numbers
        c.lucky_numbers
        self.assertLessEqual(c.get_dict_value_cache_free.call_count, 1)

    def test_set_dict_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'), default={'a': 1, 'b': 2, 'c': 3}, allow_cache=True)

        c = MyConfig.get_instance()
        c.set_dict_value_cache_free = MagicMock(return_value={'a': 1, 'b': 2, 'c': 3})
        c.lucky_numbers = {'a': 1, 'b': 2, 'c': 3}
        c.lucky_numbers = {'a': 1, 'b': 2, 'c': 3}
        c.lucky_numbers = {'a': 1, 'b': 2, 'c': 3}
        self.assertLessEqual(c.set_dict_value_cache_free.call_count, 1)

    def test_del_value_is_cached(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'), default={'a': 1, 'b': 2, 'c': 3}, allow_cache=True)

        c = MyConfig.get_instance()
        c.del_value_cache_free = MagicMock()

        del c.lucky_numbers
        del c.lucky_numbers
        del c.lucky_numbers
        self.assertLessEqual(c.del_value_cache_free.call_count, 1)

    def test_set_value_writes_new_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=True)

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        c.first_name = 'Konstantin'
        c.first_name = 'Kirill'
        self.assertEqual(c.get_value_cache_free('FirstName'), 'Kirill')

    def test_set_array_value_writes_new_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = ArrayOption('LuckyNumber', IntOption('_'), default=(1, 2, 3), allow_cache=True)

        c = MyConfig.get_instance()
        c.lucky_numbers = [4, 5, 6]
        c.lucky_numbers = [7, 8, 9]
        c.lucky_numbers = [10, 11, 12]
        self.assertEqual(c.get_array_value_cache_free('LuckyNumber'), ['10', '11', '12'])

    def test_set_dict_value_writes_new_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'), default={'a': 1, 'b': 2, 'c': 3}, allow_cache=True)

        c = MyConfig.get_instance()
        c.lucky_numbers = {'a': 4, 'b': 5, 'c': 6}
        c.lucky_numbers = {'a': 7, 'b': 8, 'c': 9}
        c.lucky_numbers = {'a': 10, 'b': 11, 'c': 12}
        self.assertEqual(c.get_dict_value_cache_free('LuckyNumber'), {'a': '10', 'b': '11', 'c': '12'})

    def test_del_value_writes_new_value(self):
        class MyConfig(self.CONFIG_TYPE):
            lucky_numbers = DictOption('LuckyNumber', IntOption('_'), default={'a': 1, 'b': 2, 'c': 3}, allow_cache=True)

        c = MyConfig.get_instance()
        c.lucky_numbers = {'a': 4, 'b': 5, 'c': 6}
        del c.lucky_numbers
        c.lucky_numbers = {'a': 10, 'b': 11, 'c': 12}
        del c.lucky_numbers
        self.assertEqual(c.get_dict_value_cache_free('LuckyNumber'), None)

    def test_allow_cache(self):
        class AllowCacheConfig(self.CONFIG_TYPE):
            ALLOW_CACHE = True
            first_name = StringOption('FirstName', default='Ilya')

        class DisallowCacheConfig(self.CONFIG_TYPE):
            ALLOW_CACHE = False
            first_name = StringOption('FirstName', default='Ilya')

        class DefaultCacheConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = AllowCacheConfig.get_instance()
        c.get_value = MagicMock(return_value='Ilya')
        c.first_name
        c.get_value.assert_called_with('FirstName', allow_cache=True)

        c = DisallowCacheConfig.get_instance()
        c.get_value = MagicMock(return_value='Ilya')
        c.first_name
        c.get_value.assert_called_with('FirstName', allow_cache=False)

        c = DefaultCacheConfig.get_instance()
        c.get_value = MagicMock(return_value='Ilya')
        c.first_name
        c.get_value.assert_called_with('FirstName', allow_cache=False)

    def test_per_option_allow_cache(self):
        class AllowCacheConfig(self.CONFIG_TYPE):
            ALLOW_CACHE = True
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        class DisallowCacheConfig(self.CONFIG_TYPE):
            ALLOW_CACHE = False
            first_name = StringOption('FirstName', default='Ilya', allow_cache=True)

        c = AllowCacheConfig.get_instance()
        c.get_value = MagicMock(return_value='Ilya')
        c.first_name
        c.get_value.assert_called_with('FirstName', allow_cache=False)

        c = DisallowCacheConfig.get_instance()
        c.get_value = MagicMock(return_value='Ilya')
        c.first_name
        c.get_value.assert_called_with('FirstName', allow_cache=True)

    def test_magic_len(self):
        class ZeroItemsConfig(self.CONFIG_TYPE):
            pass

        class OneItemConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        class TwoItemsConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)
            last_name = StringOption('LastName', default='Kulakov', allow_cache=False)

        self.assertEqual(len(ZeroItemsConfig.get_instance()), len(ZeroItemsConfig._ordered_options))
        self.assertEqual(len(OneItemConfig.get_instance()), len(OneItemConfig._ordered_options))
        self.assertEqual(len(TwoItemsConfig.get_instance()), len(TwoItemsConfig._ordered_options))

    def test_magic_getitem(self):
        class OneItemConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        c = OneItemConfig.get_instance()
        self.assertEqual(c['FirstName'], c.first_name)

        with self.assertRaises(KeyError):
            c['SecondName']

    def test_magic_setitem(self):
        class OneItemConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        c = OneItemConfig.get_instance()
        c['FirstName'] = 'Tamara'
        self.assertEqual(c.first_name, 'Tamara')

        with self.assertRaises(KeyError):
            c['LastName'] = 'Fedorova'

    def test_magic_delitem(self):
        class OneItemConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        c = OneItemConfig.get_instance()
        c['FirstName'] = 'Tamara'
        self.assertEqual(c.first_name, 'Tamara')
        del c['FirstName']
        self.assertEqual(c.first_name, 'Ilya')

    def test_magic_iter(self):
        class OneItemConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', allow_cache=False)

        c = OneItemConfig.get_instance()
        self.assertSetEqual(set(c.keys()), set(iter(c)))

    def test_reset_clears_cache(self):
        class MyConfig(self.CONFIG_TYPE):
            age = IntOption('Age', default=42)

        c = MyConfig()
        c.age = 99
        self.assertEqual(c._cache['Age'], '99')
        c.reset()
        self.assertEqual(c._cache['Age'], None)

    def test_option_mixins(self):
        class MyConfigMixin:
            age = IntOption('Age', default=42)

        class MyConfig(MyConfigMixin, self.CONFIG_TYPE):
            pass

        c = MyConfig()
        self.assertIn('Age', c)

    @abstractmethod
    def test_config_is_created_if_not_found(self):
        pass
