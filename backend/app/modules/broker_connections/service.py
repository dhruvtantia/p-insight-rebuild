import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.db.models import BrokerConnection, User
from app.modules.broker_connections.schemas import (
    BrokerConnectionCreate,
    BrokerConnectionResponse,
    BrokerProviderPlaceholder,
)

BROKER_PROVIDERS = [
    BrokerProviderPlaceholder(
        provider="plaid",
        display_name="Plaid",
        status="coming_soon",
        message="Bank and brokerage aggregation is planned after manual upload workflows stabilize.",
    ),
    BrokerProviderPlaceholder(
        provider="zerodha",
        display_name="Zerodha",
        status="coming_soon",
        message="Zerodha sync is planned for a later India brokerage phase.",
    ),
    BrokerProviderPlaceholder(
        provider="ibkr",
        display_name="IBKR",
        status="coming_soon",
        message="Interactive Brokers sync is planned for advanced portfolios.",
    ),
    BrokerProviderPlaceholder(
        provider="alpaca",
        display_name="Alpaca",
        status="coming_soon",
        message="Alpaca connection support is planned for a later broker sync phase.",
    ),
]


class BrokerConnectionNotFoundError(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Broker connection not found")


class BrokerConnectionService:
    def __init__(self, db: Session):
        self.db = db

    def list_connections(self, *, user: User) -> list[BrokerConnectionResponse]:
        connections = list(
            self.db.scalars(
                select(BrokerConnection).where(BrokerConnection.user_id == user.id).order_by(BrokerConnection.created_at.desc())
            ).all()
        )
        return [self._response(connection) for connection in connections]

    def create_placeholder(self, *, user: User, data: BrokerConnectionCreate) -> BrokerConnectionResponse:
        metadata = {
            "message": "Broker sync is coming soon. Manual uploads remain the supported MVP import path.",
            "is_placeholder": True,
        }
        connection = BrokerConnection(
            user_id=user.id,
            provider=data.provider,
            status="waitlist_interest",
            metadata_json=json.dumps(metadata, sort_keys=True),
        )
        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)
        return self._response(connection)

    def delete_connection(self, *, user: User, connection_id: str) -> None:
        connection = self.db.scalar(
            select(BrokerConnection).where(BrokerConnection.user_id == user.id, BrokerConnection.id == connection_id)
        )
        if connection is None:
            raise BrokerConnectionNotFoundError()
        self.db.delete(connection)
        self.db.commit()

    def provider_placeholders(self) -> list[BrokerProviderPlaceholder]:
        return BROKER_PROVIDERS

    def _response(self, connection: BrokerConnection) -> BrokerConnectionResponse:
        metadata = json.loads(connection.metadata_json or "{}")
        return BrokerConnectionResponse(
            id=connection.id,
            provider=connection.provider,
            status=connection.status,
            message=metadata.get("message", "Broker sync is coming soon."),
            metadata=metadata,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
