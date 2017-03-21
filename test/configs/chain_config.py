from collections import OrderedDict
import os
import unittest.mock
import uuid

from nativeconfig import ChainConfig, MemoryConfig, IntOption, StringOption


class TestChainConfig(unittest.TestCase):
    OPTION_ENV_NAME = str(uuid.uuid4())

    def tearDown(self):
        os.environ.pop(self.OPTION_ENV_NAME, None)

    def test_configs_must_be_OrderedDict(self):
        with self.assertRaises(ValueError):
            ChainConfig({})

    def test_undefined_config_raises(self):
        c = ChainConfig(OrderedDict())

        with self.assertRaises(AttributeError):
            c.age

        class AConfig(MemoryConfig):
            age = IntOption('_')

        c = ChainConfig(OrderedDict(a=AConfig.get_instance()))

        with self.assertRaises(AttributeError):
            c.height

    def test_order_of_resolution(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = IntOption('_')

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        b.age = 42
        self.assertEqual(c.age, 42)

        a.age = 9000
        self.assertEqual(c.age, 9000)

        del a.age
        self.assertEqual(c.age, 42)

    def test_intermediate_default_values_ignored(self):
        class AConfig(MemoryConfig):
            age = IntOption('_', default=42)

        class BConfig(MemoryConfig):
            age = IntOption('_')

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        b.age = 9000
        self.assertEqual(c.age, 9000)

        a.age = 42
        self.assertEqual(c.age, 42)

        del a.age
        self.assertEqual(c.age, 9000)

    def test_unset_option_uses_firts_default(self):
        class AConfig(MemoryConfig):
            age = IntOption('_', default=42)

        class BConfig(MemoryConfig):
            age = IntOption('_', default=9000)

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        self.assertEqual(c.age, 42)

        b.age = 0xdeadbeef
        self.assertEqual(c.age, 0xdeadbeef)

    def test_env_value_is_recognized_before_default(self):
        class AConfig(MemoryConfig):
            age = IntOption('_', default=42)

        class BConfig(MemoryConfig):
            age = IntOption('_', default=9000, env_name=self.OPTION_ENV_NAME)

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        self.assertEqual(c.age, 42)

        os.environ[self.OPTION_ENV_NAME] = BConfig.age.serialize_json(0xdeadbeef)
        self.assertEqual(c.age, 0xdeadbeef)

    def test_temp_value(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = IntOption('_')

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        c.temporary.age = 0xdeadbeef
        self.assertEqual(c.age, 0xdeadbeef)

    def test_temp_value_with_env(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = IntOption('_', env_name=self.OPTION_ENV_NAME)

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        c.temporary.age = 0xdeadbeef
        self.assertEqual(c.age, 0xdeadbeef)

        os.environ[self.OPTION_ENV_NAME] = '42'
        self.assertEqual(c.age,  0xdeadbeef)

        del c.temporary.age
        self.assertEqual(c.age, 42)

    def test_temp_takes_options_from_first_appearance(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = IntOption('_', env_name=self.OPTION_ENV_NAME)

        a = AConfig.get_instance()
        b = BConfig.get_instance()
        c = ChainConfig(OrderedDict([('a', a), ('b', b)]))

        self.assertEqual(c.temporary.__class__.age, AConfig.age)

    def test_option_type_mismatch_raises(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = StringOption('_')

        with self.assertRaises(ValueError):
            ChainConfig(OrderedDict([('a', AConfig.get_instance()), ('b', BConfig.get_instance())]))

    def test_option_name_mismatch_raises(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            age = IntOption('Age')

        with self.assertRaises(ValueError):
            ChainConfig(OrderedDict([('a', AConfig.get_instance()), ('b', BConfig.get_instance())]))

    def test_option_attibute_name_mismatch_raises(self):
        class AConfig(MemoryConfig):
            age = IntOption('_')

        class BConfig(MemoryConfig):
            height = IntOption('_')

        with self.assertRaises(AttributeError):
            ChainConfig(OrderedDict([('a', AConfig.get_instance()), ('b', BConfig.get_instance())]))
