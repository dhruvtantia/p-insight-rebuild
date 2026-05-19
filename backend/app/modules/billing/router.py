from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.db.session import get_db
from app.modules.billing.schemas import BillingPlanResponse, BillingWebhookResponse, CheckoutSessionResponse
from app.modules.billing.service import BillingService

router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_billing_service(db: Annotated[Session, Depends(get_db)]) -> BillingService:
    return BillingService(db)


BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]


@router.get("/plan", response_model=BillingPlanResponse)
def get_plan(user: CurrentUser, service: BillingServiceDep):
    return service.get_plan(user=user)


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(user: CurrentUser, service: BillingServiceDep):
    return service.create_checkout_session(user=user)


@router.post("/webhook", response_model=BillingWebhookResponse)
def billing_webhook(service: BillingServiceDep):
    return service.handle_webhook()
