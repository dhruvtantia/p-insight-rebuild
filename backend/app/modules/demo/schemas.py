from pydantic import BaseModel


class DemoSeedResponse(BaseModel):
    portfolio_id: str
    portfolio_name: str
    holdings_count: int
    symbols: list[str]
    message: str
