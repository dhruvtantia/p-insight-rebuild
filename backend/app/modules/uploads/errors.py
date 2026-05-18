from app.core.errors import NotFoundError, ValidationAppError


class UploadJobNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Upload job not found")


class UploadValidationError(ValidationAppError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
