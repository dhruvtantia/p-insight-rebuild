from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.feature_flags import require_feature_enabled
from app.db.session import get_db
from app.modules.snapshots.schemas import SnapshotCompareResponse, SnapshotCreate, SnapshotResponse, SnapshotSummary
from app.modules.snapshots.service import SnapshotService

router = APIRouter(prefix="/api/portfolios/{portfolio_id}/snapshots", tags=["snapshots"])


def require_snapshots_enabled() -> None:
    require_feature_enabled("ENABLE_SNAPSHOTS")


def get_snapshot_service(db: Annotated[Session, Depends(get_db)]) -> SnapshotService:
    return SnapshotService(db)


SnapshotServiceDep = Annotated[SnapshotService, Depends(get_snapshot_service)]


@router.post("", response_model=SnapshotResponse, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    portfolio_id: str,
    _: Annotated[None, Depends(require_snapshots_enabled)],
    user: CurrentUser,
    service: SnapshotServiceDep,
    data: SnapshotCreate | None = None,
):
    return service.create_snapshot(
        portfolio_id=portfolio_id,
        user=user,
        data=data or SnapshotCreate(),
    )


@router.get("", response_model=list[SnapshotSummary])
def list_snapshots(
    portfolio_id: str,
    _: Annotated[None, Depends(require_snapshots_enabled)],
    user: CurrentUser,
    service: SnapshotServiceDep,
):
    return service.list_snapshots(portfolio_id=portfolio_id, user=user)


@router.get("/compare", response_model=SnapshotCompareResponse)
def compare_snapshots(
    portfolio_id: str,
    from_id: Annotated[str, Query(min_length=1)],
    to_id: Annotated[str, Query(min_length=1)],
    _: Annotated[None, Depends(require_snapshots_enabled)],
    user: CurrentUser,
    service: SnapshotServiceDep,
):
    return service.compare_snapshots(
        portfolio_id=portfolio_id,
        user=user,
        from_id=from_id,
        to_id=to_id,
    )
