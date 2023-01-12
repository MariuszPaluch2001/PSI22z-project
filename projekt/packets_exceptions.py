class TooLongDataError(Exception):
    def __init__(self) -> None:
        self.message = "Data length exceeded 100 characters."
        super().__init__(self.message)
