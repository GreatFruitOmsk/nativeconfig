import logging

import objc
import traceback

from nativeconfig.config.base_config import BaseConfig


LOG = logging.getLogger('nativeconfig')


class NSUserDefaultsConfig(BaseConfig):
    """
    Store config in user defaults.

    allow_cache is ignored, since NSUserDefaults already provides caching.

    @cvar NSUSERDEFAULTS_SUITE: Name of the suite for shared apps.
    """
    LOG = LOG.getChild('NSUserDefaultsConfig')

    NSUSERDEFAULTS_SUITE = None

    def __init__(self):
        if self.NSUSERDEFAULTS_SUITE is not None:
            self._user_defaults = objc.lookUpClass('NSUserDefaults').alloc().initWithSuiteName_(self.NSUSERDEFAULTS_SUITE)
        else:
            self._user_defaults = objc.lookUpClass('NSUserDefaults').standardUserDefaults()

        self._nsstring_class = objc.lookUpClass('NSString')
        self._nsarray_class = objc.lookUpClass('NSArray')
        self._nsdictionary_class = objc.lookUpClass('NSDictionary')

        self._copy_str = lambda x: self._nsstring_class.stringWithString_(x)
        self._copy_array = lambda x: self._nsarray_class.arrayWithArray_([self._copy_str(str(v)) for v in x])
        self._copy_dict = lambda x: self._nsdictionary_class.dictionaryWithDictionary_({self._copy_str(str(k)): self._copy_str(str(v)) for k, v in x.items()})

        super(NSUserDefaultsConfig, self).__init__()

    #{ BaseConfig

    def get_value_cache_free(self, name):
        with objc.autorelease_pool():
            try:
                v = self._user_defaults.stringForKey_(self._copy_str(name))
                return str(v) if v is not None else None
            except:
                pass

        return None

    def set_value_cache_free(self, name, raw_value):
        with objc.autorelease_pool():
            try:
                if raw_value is not None:
                    self._user_defaults.setObject_forKey_(self._copy_str(raw_value), self._copy_str(name))
                    self._user_defaults.synchronize()
                else:
                    self.del_value_cache_free(self._copy_str(name))
            except:
                self.LOG.exception("Unable to set '%s' in the user defaults:", name)

    def del_value_cache_free(self, name):
        with objc.autorelease_pool():
            try:
                self._user_defaults.removeObjectForKey_(self._copy_str(name))
                self._user_defaults.synchronize()
            except:
                self.LOG.exception("Unable to delete '%s' from the user defaults:", name)

    def get_array_value_cache_free(self, name, allow_cache=False):
        with objc.autorelease_pool():
            try:
                v = self._user_defaults.arrayForKey_(self._copy_str(name))
                return [str(i) for i in v] if v is not None else None
            except:
                pass

        return None

    def set_array_value_cache_free(self, name, value):
        with objc.autorelease_pool():
            try:
                if value is not None:
                    self._user_defaults.setObject_forKey_(self._copy_array(value), self._copy_str(name))
                    self._user_defaults.synchronize()
                else:
                    self.del_value_cache_free(self._copy_str(name))
            except:
                self.LOG.exception("Unable to set array '%s' in the user defaults:", name)

    def get_dict_value_cache_free(self, name, allow_cache=False):
        with objc.autorelease_pool():
            try:
                v = self._user_defaults.dictionaryForKey_(self._copy_str(name))
                return {str(k): str(i) for k, i in v.items()} if v is not None else None
            except:
                pass

        return None

    def set_dict_value_cache_free(self, name, value):
        with objc.autorelease_pool():
            try:
                if value is not None:
                    self._user_defaults.setObject_forKey_(self._copy_dict(value), self._copy_str(name))
                    self._user_defaults.synchronize()
                else:
                    self.del_value_cache_free(self._copy_str(name))
            except:
                self.LOG.exception("Unable to set dict '%s' in the user defaults:", name)

    #}
