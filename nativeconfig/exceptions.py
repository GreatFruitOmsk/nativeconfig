class Error(Exception):
    pass


class InitializationError(Error):
    def __init__(self, msg):
        super().__init__(msg)


class OptionError(Error):
    def __init__(self, msg, option_name):
        self.option_name = option_name
        super().__init__(msg)


class ValidationError(OptionError):
    def __init__(self, msg, value, option_name):
        self.value = value
        super().__init__(msg, option_name)


class SerializationError(OptionError):
    def __init__(self, msg, value, option_name):
        self.value = value
        super().__init__(msg, option_name)


class DeserializationError(OptionError):
    def __init__(self, msg, raw_value, option_name):
        self.raw_value = raw_value
        super().__init__(msg, option_name)
