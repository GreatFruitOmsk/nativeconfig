import sys

from nativeconfig.config.memory_config import MemoryConfig
from nativeconfig.config.json_config import JSONConfig

if sys.platform.startswith('win32'):
    from nativeconfig.config.registry_config import RegistryConfig
    PreferredConfig = RegistryConfig
elif sys.platform.startswith('darwin'):
    try:
        from nativeconfig.config.nsuserdefaults_config import NSUserDefaultsConfig
        PreferredConfig = NSUserDefaultsConfig
    except ImportError:
        PreferredConfig = JSONConfig
else:
    PreferredConfig = JSONConfig
