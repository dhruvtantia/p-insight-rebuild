from app.core.errors import NotFoundError


class HoldingNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Holding not found")
