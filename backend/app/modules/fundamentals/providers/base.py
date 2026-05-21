from abc import ABC, abstractmethod

from app.modules.fundamentals.schemas import FundamentalsResponse


class FundamentalsProvider(ABC):
    source: str

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        raise NotImplementedError
