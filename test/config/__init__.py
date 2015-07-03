from abc import ABC, abstractmethod
import json
import os
from unittest.mock import MagicMock

from nativeconfig.options import StringOption, IntOption, ArrayOption, DictOption
from nativeconfig.exceptions import InitializationError, DeserializationError, ValidationError


class TestConfigMixin(ABC):
    CONFIG_TYPE = None

    def tearDown(self):
        if 'FIRST_NAME' in os.environ:
            del os.environ['FIRST_NAME']

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

    def test_get_value_for_option_name_returns_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        self.assertEqual(json.loads(c.get_value_for_option_name('FirstName')), 'Ilya')

    def test_get_value_for_option_returns_None_and_raises_warn_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertWarns(UserWarning):
            self.assertEqual(c.get_value_for_option_name('LastName'), None)

    def test_set_value_for_option_name_accepts_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.set_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Artem')

        with self.assertRaises(DeserializationError):
            c.set_value_for_option_name('FirstName', 'Artem')

    def test_set_null_value_for_option_name_deletes_value(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.first_name = 'Artem'
        self.assertEqual(c.get_value_for_option_name('FirstName'), '"Artem"')
        c.set_value_for_option_name('FirstName', json.dumps(None))
        self.assertEqual(c.get_value('FirstName'), None)

    def test_set_value_for_option_name_raises_warn_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertWarns(UserWarning):
            c.set_value_for_option_name('LastName', 'Kulakov')

    def test_set_one_shot_value_for_option_name_accepts_json(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        c.set_one_shot_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Artem')

        with self.assertRaises(DeserializationError):
            c.set_one_shot_value_for_option_name('FirstName', 'Artem')

    def test_set_one_shot_value_for_option_name_raises_warn_if_option_not_found(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()

        with self.assertWarns(UserWarning):
            c.set_one_shot_value_for_option_name('LastName', 'Kulakov')

    def test_one_shot_value_overrides_config(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_value_for_option_name('FirstName', json.dumps('Artem'))

        c.set_one_shot_value_for_option_name('FirstName', json.dumps('Ivan'))
        self.assertEqual(c.first_name, 'Ivan')

    def test_one_shot_value_does_not_override_env(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya', env_name='FIRST_NAME')

        c = MyConfig.get_instance()
        os.environ['FIRST_NAME'] = json.dumps('Ivan')
        c.set_one_shot_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Ivan')

    def test_one_shot_value_reset_by_set(self):
        class MyConfig(self.CONFIG_TYPE):
            first_name = StringOption('FirstName', default='Ilya')

        c = MyConfig.get_instance()
        c.set_one_shot_value_for_option_name('FirstName', json.dumps('Artem'))
        self.assertEqual(c.first_name, 'Artem')
        c.first_name = 'Ivan'
        self.assertEqual(c.first_name, 'Ivan')

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

        with self.assertWarns(UserWarning):
            c.del_value_for_option_name('LastName')

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
        self.assertIsInstance(c.resolve_value.call_args[0][0], DeserializationError)
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

    def test_overriding_base_option_moves_it_the_end(self):
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

    @abstractmethod
    def test_config_is_created_if_not_found(self):
        pass
