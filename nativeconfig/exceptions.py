class Error(Exception):
    pass


class InitializationError(Error):
    def __init__(self, msg):
        super().__init__(msg)


class ValidationError(Error):
    def __init__(self, msg, value, option_name):
        self.value = value
        self.option_name = option_name
        super().__init__(msg)


class SerializationError(Error):
    def __init__(self, msg, value):
        self.value = value
        super().__init__(msg)


class DeserializationError(Error):
    def __init__(self, msg, raw_value):
        self.raw_value = raw_value
        super().__init__(msg)
