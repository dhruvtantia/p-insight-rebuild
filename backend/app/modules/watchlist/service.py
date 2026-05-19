import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationAppError
from app.db.models import AssetPrice, User, WatchlistItem
from app.modules.watchlist.schemas import WatchlistCreate, WatchlistItemResponse


class WatchlistItemNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Watchlist item not found")


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db

    def list_items(self, *, user: User) -> list[WatchlistItemResponse]:
        items = list(
            self.db.scalars(
                select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.created_at.desc())
            ).all()
        )
        latest_prices = self._latest_prices_by_symbol([item.symbol for item in items])
        return [self._response(item=item, latest_price=latest_prices.get(item.symbol)) for item in items]

    def create_item(self, *, user: User, data: WatchlistCreate) -> WatchlistItemResponse:
        existing = self.db.scalar(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.symbol == data.symbol)
        )
        if existing is not None:
            raise ValidationAppError("Symbol is already on the watchlist")

        item = WatchlistItem(user_id=user.id, symbol=data.symbol, note=self._encode_note(name=data.name, notes=data.notes))
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        latest_price = self._latest_prices_by_symbol([item.symbol]).get(item.symbol)
        return self._response(item=item, latest_price=latest_price)

    def delete_item(self, *, user: User, watchlist_item_id: str) -> None:
        item = self.db.scalar(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id, WatchlistItem.id == watchlist_item_id)
        )
        if item is None:
            raise WatchlistItemNotFoundError()
        self.db.delete(item)
        self.db.commit()

    def _latest_prices_by_symbol(self, symbols: list[str]) -> dict[str, AssetPrice]:
        if not symbols:
            return {}
        statement = (
            select(AssetPrice)
            .where(AssetPrice.symbol.in_(symbols))
            .order_by(AssetPrice.symbol.asc(), AssetPrice.as_of.desc(), AssetPrice.created_at.desc())
        )
        prices: dict[str, AssetPrice] = {}
        for price in self.db.scalars(statement).all():
            if price.symbol not in prices:
                prices[price.symbol] = price
        return prices

    def _response(self, *, item: WatchlistItem, latest_price: AssetPrice | None) -> WatchlistItemResponse:
        return WatchlistItemResponse(
            id=item.id,
            user_id=item.user_id,
            symbol=item.symbol,
            name=self._decode_note(item.note)["name"],
            notes=self._decode_note(item.note)["notes"],
            current_price=float(latest_price.price) if latest_price is not None else None,
            price_currency=latest_price.currency if latest_price is not None else None,
            price_source=latest_price.source if latest_price is not None else None,
            price_as_of=latest_price.as_of if latest_price is not None else None,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )

    def _encode_note(self, *, name: str | None, notes: str | None) -> str:
        return json.dumps({"name": name, "notes": notes}, sort_keys=True)

    def _decode_note(self, raw_note: str | None) -> dict[str, str | None]:
        if raw_note is None:
            return {"name": None, "notes": None}
        try:
            data = json.loads(raw_note)
        except json.JSONDecodeError:
            return {"name": None, "notes": raw_note}
        if not isinstance(data, dict):
            return {"name": None, "notes": raw_note}
        return {
            "name": data.get("name") if isinstance(data.get("name"), str) else None,
            "notes": data.get("notes") if isinstance(data.get("notes"), str) else None,
        }
