from app.core.errors import NotFoundError


class PortfolioNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Portfolio not found")
