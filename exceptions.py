# Custom Errors...


class FileSysError(Exception):

    def __init__(self, message, errors):

        # Call the base class constructor with the parameters it needs
        super().__init__(message)
