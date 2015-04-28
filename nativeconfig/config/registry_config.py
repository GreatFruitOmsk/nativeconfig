import logging
import sys
import winreg

from nativeconfig.config.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')

ERROR_NO_MORE_ITEMS = 259
ERROR_NO_MORE_FILES = 18


def _traverse_registry_key(key, sub_key):
    """
    Traverse registry key and yield one by one.

    @raise WindowsError: If key cannot be opened (e.g. does not exist).
    """
    current_key = winreg.OpenKey(key, sub_key, 0, winreg.KEY_ALL_ACCESS)

    try:
        i = 0
        while True:
            next_key = winreg.EnumKey(current_key, i)
            for k in _traverse_registry_key(key, r'{}\{}'.format(sub_key, next_key)):
                yield k
            i += 1
    except WindowsError:
        yield sub_key


class RegistryConfig(BaseConfig):
    LOG = LOG.getChild('RegistryConfig')
    REGISTRY_KEY = winreg.HKEY_CURRENT_USER

    def __init__(self):
        super(RegistryConfig, self).__init__()

        k = winreg.CreateKey(self.REGISTRY_KEY, self.CONFIG_PATH)
        winreg.CloseKey(k)

    def get_value(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.CONFIG_PATH) as app_key:
                try:
                    return str(winreg.QueryValueEx(app_key, name)[0])
                except:
                    self.LOG.info("Unable to get '%s' from the registry:", name, exc_info=True)
        except:
            self.LOG.exception("Unable to access registry:")

        return None

    def set_value(self, name, raw_value):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.CONFIG_PATH, 0, winreg.KEY_WRITE) as app_key:
                try:
                    winreg.SetValueEx(app_key, name, 0, winreg.REG_SZ, str(raw_value))
                except:
                    self.LOG.exception("Unable to set '%s' in the registry:", name)
        except:
            self.LOG.exception("Unable to access registry:")

    def del_value(self, name):
        try:
            try:
                for k in _traverse_registry_key(self.REGISTRY_KEY, r'{}\{}'.format(self.CONFIG_PATH, name)):
                    winreg.DeleteKey(self.REGISTRY_KEY, k)
            except WindowsError:
                try:
                    with winreg.OpenKey(self.REGISTRY_KEY, self.CONFIG_PATH, 0, winreg.KEY_ALL_ACCESS) as app_key:
                        winreg.DeleteValue(app_key, name)
                except WindowsError:
                    self.LOG.info("Unable to delete '%s' from the registry:", name)
        except:
            self.LOG.exception("Unable to access registry:")

    def get_array_value(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.CONFIG_PATH) as app_key:
                try:
                    return [str(v) for v in winreg.QueryValueEx(app_key, name)[0]]
                except:
                    self.LOG.info("Unable to get array '%s' from the registry:", name, exc_info=True)
        except:
            self.LOG.exception("Unable to access registry:")

        return None

    def set_array_value(self, name, value):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.CONFIG_PATH, 0, winreg.KEY_WRITE) as app_key:
                try:
                    winreg.SetValueEx(app_key, name, 0, winreg.REG_MULTI_SZ, [str(v) for v in value])
                except:
                    self.LOG.exception("Unable to set '%s' in the registry:", name)
        except:
            self.LOG.exception("Unable to access registry:")

    def get_dict_value(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, r'{}\{}'.format(self.CONFIG_PATH, key), 0, winreg.KEY_ALL_ACCESS) as app_key:
                v = {}

                try:
                    i = 0
                    while True:
                        name, value, _value_type = winreg.EnumValue(app_key, i)

                        if value is not None:
                            v[name] = str(value)

                        i += 1
                except WindowsError as e:
                    if e.winerror != ERROR_NO_MORE_ITEMS and e.winerror != ERROR_NO_MORE_FILES:
                        raise
                    else:
                        pass  # end of keys
                except:
                    self.LOG.exception("Error during registry enumeration:")
                    return None

            return v
        except:
            self.LOG.info("Unable to get dict '%s' from the registry:")

        return None

    def set_dict_value(self, name, value):
        try:
            with winreg.CreateKey(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, name)) as dict_key:
                try:
                    for k, v in value.items():
                        winreg.SetValueEx(dict_key, str(k), 0, winreg.REG_SZ, str(v))
                except:
                    self.LOG.exception("Unable to access registry:")
        except:
            self.LOG.exception("Unable to access registry:")
