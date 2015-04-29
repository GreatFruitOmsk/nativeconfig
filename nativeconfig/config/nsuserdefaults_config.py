import logging

import objc

from nativeconfig.config.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')


class NSUserDefaultsConfig(BaseConfig):
    """
    Store config in user defaults.

    @cvar NSUSERDEFAULTS_SUITE: Name of the suite for shared apps.
    """
    LOG = LOG.getChild('NSUserDefaultsConfig')

    NSUSERDEFAULTS_SUITE = None

    def __init__(self):
        if self.NSUSERDEFAULTS_SUITE is not None:
            self._user_defaults = objc.lookUpClass('NSUserDefaults').alloc().initWithSuiteName_(self.NSUSERDEFAULTS_SUITE)
        else:
            self._user_defaults = objc.lookUpClass('NSUserDefaults').standardUserDefaults()

        super(NSUserDefaultsConfig, self).__init__()

    def get_value(self, name):
        try:
            v = self._user_defaults.stringForKey_(name)
            return str(v) if v is not None else None
        except:
            pass

        return None

    def set_value(self, name, raw_value):
        try:
            self._user_defaults.setObject_forKey_(raw_value, name)
        except:
            self.LOG.exception("Unable to set '%s' in the user defaults:", name)

    def del_value(self, name):
        try:
            self._user_defaults.removeObjectForKey_(name)
        except:
            self.LOG.exception("Unable to delete '%s' from the user defaults:", name)

    def get_array_value(self, name):
        try:
            v = self._user_defaults.arrayForKey_(name)
            return [str(i) for i in v] if v is not None else None
        except:
            pass

        return None

    def set_array_value(self, name, value):
        try:
            if value is not None:
                self._user_defaults.setObject_forKey_([str(v) for v in value], name)
            else:
                self.del_value(name)
        except:
            self.LOG.exception("Unable to set array '%s' in the user defaults:", name)

    def get_dict_value(self, name):
        try:
            v = self._user_defaults.dictionaryForKey_(name)
            return {str(k): str(i) for k, i in v.items()} if v is not None else None
        except:
            pass

        return None

    def set_dict_value(self, name, value):
        try:
            if value is not None:
                self._user_defaults.setObject_forKey_({str(k): str(v) for k, v in value.items()}, name)
            else:
                self.del_value(name)
        except:
            self.LOG.exception("Unable to set dict '%s' in the user defaults:", name)
