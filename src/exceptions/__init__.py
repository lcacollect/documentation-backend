class AuthenticationError(LookupError):
    pass


class MicroServiceConnectionError(ConnectionError):
    pass


class MicroServiceResponseError(Exception):
    pass


class SourceElementCreationError(Exception):
    pass
