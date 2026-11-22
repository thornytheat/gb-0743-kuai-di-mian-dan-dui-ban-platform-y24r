class DomainError(Exception):
    def __init__(self, code, status=422, **details):
        super().__init__(code)
        self.code, self.status, self.details = code, status, details
