from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.demo.schemas import DemoSeedResponse
from app.modules.demo.service import DemoSeedService

router = APIRouter(prefix="/api/demo", tags=["demo"])


def get_demo_seed_service(db: Annotated[Session, Depends(get_db)]) -> DemoSeedService:
    return DemoSeedService(db)


DemoSeedServiceDep = Annotated[DemoSeedService, Depends(get_demo_seed_service)]


@router.post("/seed", response_model=DemoSeedResponse)
def seed_demo_portfolio(user: CurrentUser, service: DemoSeedServiceDep):
    return service.seed_for_user(user=user)
