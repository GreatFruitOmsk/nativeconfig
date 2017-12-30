import unittest

try:
    from nativeconfig.configs import NSUserDefaultsConfig
except ImportError:
    pass
else:
    from test.configs import ConfigMixin


    class MyNSUserDefaultsConfig(NSUserDefaultsConfig):
        NSUSERDEFAULTS_SUITE = 'nativeconfig'


    class TestNSUserDefaultsConfig(ConfigMixin, unittest.TestCase):
        CONFIG_TYPE = MyNSUserDefaultsConfig

        def setUp(self):
            try:
                c = self.CONFIG_TYPE.get_instance()
                domain = self.CONFIG_TYPE.NSUSERDEFAULTS_SUITE
                c._user_defaults.removePersistentDomainForName_(c._copy_str(domain))
            except OSError:
                pass

            super().setUp()

        def test_config_is_created_if_not_found(self):
            pass
