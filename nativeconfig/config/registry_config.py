import logging
import winreg

from nativeconfig.config.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')

ERROR_NO_MORE_ITEMS = 259
ERROR_NO_MORE_FILES = 18


def traverse_registry_key(key, sub_key):
    """
    Traverse registry key and yield one by one.

    @raise WindowsError: If key cannot be opened (e.g. does not exist).
    """
    current_key = winreg.OpenKey(key, sub_key, 0, winreg.KEY_ALL_ACCESS)

    try:
        i = 0

        while True:
            next_key = winreg.EnumKey(current_key, i)

            for k in traverse_registry_key(key, r'{}\{}'.format(sub_key, next_key)):
                yield k

            i += 1
    except OSError:
        yield sub_key


class RegistryConfig(BaseConfig):
    """
    Store config in Windows Registry.

    @cvar REGISTRY_KEY: Key in the registry where config will be stored.
    @cvar REGISTRY_PATH: Path relative to REGISTRY_KEY that points to the config.
    """
    LOG = LOG.getChild('RegistryConfig')
    REGISTRY_KEY = winreg.HKEY_CURRENT_USER

    def __init__(self):
        k = winreg.CreateKey(self.REGISTRY_KEY, self.REGISTRY_PATH)
        winreg.CloseKey(k)

        super(RegistryConfig, self).__init__()

    #{ BaseConfig

    def get_value_cache_free(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH) as app_key:
                try:
                    value, value_type = winreg.QueryValueEx(app_key, name)

                    if not value_type == winreg.REG_SZ:
                        raise ValueError("Value must be of REG_SZ type!")

                    return value
                except OSError:
                    pass
        except:
            self.LOG.exception("Unable to get \"%s\" from the registry:", name)

        return None

    def set_value_cache_free(self, name, raw_value):
        try:
            if raw_value is not None:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_WRITE) as app_key:
                    winreg.SetValueEx(app_key, name, 0, winreg.REG_SZ, raw_value)
            else:
                self.del_value_cache_free(name)
        except:
            self.LOG.exception("Unable to set \"%s\" in the registry:", name)

    def del_value_cache_free(self, name):
        try:
            try:
                for k in traverse_registry_key(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, name)):
                    winreg.DeleteKey(self.REGISTRY_KEY, k)
            except OSError:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as app_key:
                    winreg.DeleteValue(app_key, name)
        except:
            self.LOG.info("Unable to delete \"%s\" from the registry:", name)

    def get_array_value_cache_free(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH) as app_key:
                value, value_type = winreg.QueryValueEx(app_key, name)

                if not value_type == winreg.REG_MULTI_SZ:
                    raise ValueError("Value must be of REG_MULTI_SZ type!")

                return value
        except:
            self.LOG.info("Unable to get array \"%s\" from the registry:", name, exc_info=True)

        return None

    def set_array_value_cache_free(self, name, value):
        try:
            if value is not None:
                with winreg.OpenKey(self.REGISTRY_KEY, self.REGISTRY_PATH, 0, winreg.KEY_WRITE) as app_key:
                    winreg.SetValueEx(app_key, name, 0, winreg.REG_MULTI_SZ, value)
            else:
                self.del_value_cache_free(name)
        except:
            self.LOG.exception("Unable to set \"%s\" in the registry:", name)

    def get_dict_value_cache_free(self, name):
        try:
            with winreg.OpenKey(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, name), 0, winreg.KEY_ALL_ACCESS) as app_key:
                v = {}

                try:
                    i = 0
                    while True:
                        name, value, value_type = winreg.EnumValue(app_key, i)

                        if value_type != winreg.REG_SZ:
                            raise ("Value must be of REG_SZ type!")

                        if value is not None:
                            v[name] = value

                        i += 1
                except OSError as e:
                    if e.winerror != ERROR_NO_MORE_ITEMS and e.winerror != ERROR_NO_MORE_FILES:
                        raise
                    else:
                        pass  # end of keys

                return v
        except:
            self.LOG.info("Unable to get dict '%s' from the registry:")

        return None

    def set_dict_value_cache_free(self, name, value):
        try:
            self.del_value_cache_free(name)

            if value is not None:
                with winreg.CreateKey(self.REGISTRY_KEY, r'{}\{}'.format(self.REGISTRY_PATH, name)) as app_key:
                    for k, v in value.items():
                        winreg.SetValueEx(app_key, k, 0, winreg.REG_SZ, v)
        except:
            self.LOG.exception("Unable to set \"%s\" in the registry:", name)

    #}
