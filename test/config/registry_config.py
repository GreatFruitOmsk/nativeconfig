import unittest
import unittest.mock
import sys

if sys.platform.startswith('win32'):
    import winreg

    from nativeconfig.config import RegistryConfig
    from nativeconfig.config.registry_config import traverse_registry_key
    from nativeconfig.options import StringOption, ArrayOption, DictOption

    from test.config import TestConfigMixin

    class MyRegistryConfig(RegistryConfig):
        REGISTRY_PATH = r'Software\test_config'

    class TestRegistryConfig(unittest.TestCase, TestConfigMixin):
        CONFIG_TYPE = MyRegistryConfig

        def tearDown(self):
            try:
                for k in traverse_registry_key(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH):
                    winreg.DeleteKey(MyRegistryConfig.REGISTRY_KEY, k)
            except OSError:
                pass

            TestConfigMixin.tearDown(self)

        def test_config_is_created_if_not_found(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            with self.assertRaises(FileNotFoundError):
                winreg.OpenKey(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH)

            MyConfig.get_instance()

            winreg.OpenKey(MyRegistryConfig.REGISTRY_KEY, MyRegistryConfig.REGISTRY_PATH)

        def test_get_value_returns_cached_value_if_allowed(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            c = MyConfig.get_instance()
            c._config['FirstName'] = 'Dmitry'
            self.assertEqual(c.get_value('FirstName', allow_cache=True), 'Dmitry')

        def test_get_array_value_returns_cached_value_if_allowed(self):
            class MyConfig(MyRegistryConfig):
                name = ArrayOption('Name', default=('Konstantin', 'Dravolin'))

            c = MyConfig.get_instance()
            c._config['Name'] = ['Ilya', 'Kulakov']
            self.assertEqual(c.get_array_value('Name', allow_cache=True), ['Ilya', 'Kulakov'])

        def test_get_dict_value_returns_cached_value_if_allowed(self):
            class MyConfig(MyRegistryConfig):
                name = DictOption('Name', default={'First': 'Artem', 'Second': 'Martynovich'})

            c = MyConfig.get_instance()
            c._config['Name'] = {'First': 'Konstantin', 'Second': 'Dravolin'}
            self.assertEqual(c.get_dict_value('Name', allow_cache=True), {'First': 'Konstantin', 'Second': 'Dravolin'})

        def test_reset_cache(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            c = MyConfig.get_instance()
            c.set_value('FirstName', 'Dmitry')

            c._config['FirstName'] = 'Artem'
            self.assertEqual(c.get_value('FirstName', allow_cache=True), 'Artem')
            c.reset_cache()
            self.assertEqual(c.get_value('FirstName'), 'Dmitry')

        def test_set_value_updates_cached_value(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            c = MyConfig.get_instance()

            c.set_value('FirstName', 'Dmitry')
            self.assertEqual(c._config['FirstName'], 'Dmitry')

            c.set_value('FirstName', 'Alexey')
            self.assertEqual(c._config['FirstName'], 'Alexey')

        def test_set_array_value_updates_cached_value(self):
            class MyConfig(MyRegistryConfig):
                name = ArrayOption('Name', default=('Konstantin', 'Dravolin'))

            c = MyConfig.get_instance()

            c.set_array_value('Name', ['Dmitry', 'Monastyrenko'])
            self.assertEqual(c._config['Name'], ['Dmitry', 'Monastyrenko'])

            c.set_array_value('Name', ['Artem', 'Martynovich'])
            self.assertEqual(c._config['Name'], ['Artem', 'Martynovich'])

        def test_set_dict_value_updated_cached_value(self):
            class MyConfig(MyRegistryConfig):
                name = DictOption('Name', default={'First': 'Artem', 'Second': 'Martynovich'})

            c = MyConfig.get_instance()

            c.set_dict_value('Name', {'First': 'Ilya', 'Second': 'Kulakov'})
            self.assertEqual(c._config['Name'], {'First': 'Ilya', 'Second': 'Kulakov'})

            c.set_dict_value('Name', {'First': 'Alexey', 'Second': 'Selikhov'})
            self.assertEqual(c._config['Name'], {'First': 'Alexey', 'Second': 'Selikhov'})

        def test_del_value_deletes_cached_value(self):
            class MyConfig(MyRegistryConfig):
                first_name = StringOption('FirstName', default='Ilya')

            c = MyConfig.get_instance()
            c.set_value('FirstName', 'Dmitry')

            self.assertEqual(c._config['FirstName'], 'Dmitry')
            c.del_value('FirstName')
            self.assertNotIn('FirstName', c._config)
