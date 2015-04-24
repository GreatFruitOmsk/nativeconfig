import sys

from nativeconfig.config.memory_config import MemoryConfig
from nativeconfig.config.json_config import JSONConfig

if sys.platform.startswith('win32'):
    from nativeconfig.config.registry import RegistryConfig

