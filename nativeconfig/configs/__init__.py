import sys

from nativeconfig.configs.memory_config import MemoryConfig
from nativeconfig.configs.json_config import JSONConfig

try:
    from nativeconfig.configs.yaml_config import YAMLConfig
except ImportError:
    pass

if sys.platform.startswith('win32'):
    from nativeconfig.configs.registry_config import RegistryConfig
    PreferredConfig = RegistryConfig
elif sys.platform.startswith('darwin'):
    try:
        from nativeconfig.configs.nsuserdefaults_config import NSUserDefaultsConfig
        PreferredConfig = NSUserDefaultsConfig
    except ImportError:
        PreferredConfig = JSONConfig
else:
    PreferredConfig = JSONConfig
