from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.watchlist.schemas import WatchlistCreate, WatchlistItemResponse
from app.modules.watchlist.service import WatchlistService

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def get_watchlist_service(db: Annotated[Session, Depends(get_db)]) -> WatchlistService:
    return WatchlistService(db)


WatchlistServiceDep = Annotated[WatchlistService, Depends(get_watchlist_service)]


@router.get("", response_model=list[WatchlistItemResponse])
def list_watchlist(user: CurrentUser, service: WatchlistServiceDep):
    return service.list_items(user=user)


@router.post("", response_model=WatchlistItemResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist_item(data: WatchlistCreate, user: CurrentUser, service: WatchlistServiceDep):
    return service.create_item(user=user, data=data)


@router.delete("/{watchlist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(watchlist_item_id: str, user: CurrentUser, service: WatchlistServiceDep):
    service.delete_item(user=user, watchlist_item_id=watchlist_item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
