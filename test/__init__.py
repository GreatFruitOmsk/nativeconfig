from nativeconfig.config import MemoryConfig


def all_casings(input_string):
    if not input_string:
        yield ""
    else:
        first = input_string[:1]
        if first.lower() == first.upper():
            for sub_casing in all_casings(input_string[1:]):
                yield first + sub_casing
        else:
            for sub_casing in all_casings(input_string[1:]):
                yield first.lower() + sub_casing
                yield first.upper() + sub_casing


class DummyMemoryConfig(MemoryConfig):
    def resolve_value(self, exception, name, raw_value):
        raise exception

    def migrate(self, version):
        super().migrate(version)
