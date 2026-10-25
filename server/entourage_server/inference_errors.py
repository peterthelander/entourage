"""Safe inference failures; raw upstream replies never become user messages."""


class InferenceError(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.public_message = message
