from nativeconfig.configs import MemoryConfig


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


class StubConfig(MemoryConfig):
    def resolve_value(self, exc_info, name, raw_value, source):
        if raw_value == "":
            return self.option_for_name(name)._default
        else:
            raise exc_info[1].with_traceback(exc_info[2])

    def migrate(self, version):
        super().migrate(version)
