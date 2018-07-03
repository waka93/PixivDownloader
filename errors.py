class MethodNotImplementedError(Exception):
    def __init__(self, message):
        self.message = message
        super(Exception, self).__init__(message)

    def __str__(self):
        return self.message
