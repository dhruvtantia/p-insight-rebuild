from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.broker_connections.schemas import (
    BrokerConnectionCreate,
    BrokerConnectionResponse,
    BrokerProviderPlaceholder,
)
from app.modules.broker_connections.service import BrokerConnectionService

router = APIRouter(prefix="/api/broker-connections", tags=["broker-connections"])


def get_broker_connection_service(db: Annotated[Session, Depends(get_db)]) -> BrokerConnectionService:
    return BrokerConnectionService(db)


BrokerConnectionServiceDep = Annotated[BrokerConnectionService, Depends(get_broker_connection_service)]


@router.get("", response_model=list[BrokerConnectionResponse])
def list_connections(user: CurrentUser, service: BrokerConnectionServiceDep):
    return service.list_connections(user=user)


@router.get("/providers", response_model=list[BrokerProviderPlaceholder])
def list_provider_placeholders(service: BrokerConnectionServiceDep):
    return service.provider_placeholders()


@router.post("/connect-placeholder", response_model=BrokerConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_placeholder_connection(
    data: BrokerConnectionCreate,
    user: CurrentUser,
    service: BrokerConnectionServiceDep,
):
    return service.create_placeholder(user=user, data=data)


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(connection_id: str, user: CurrentUser, service: BrokerConnectionServiceDep):
    service.delete_connection(user=user, connection_id=connection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
