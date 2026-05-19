from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Subscription, User
from app.modules.billing.schemas import BillingPlanOption, BillingPlanResponse, BillingWebhookResponse, CheckoutSessionResponse
from app.modules.usage.service import FeatureUsageSnapshotService


PLAN_OPTIONS = [
    BillingPlanOption(
        id="free",
        name="Free",
        price_label="$0",
        features=[
            "1 portfolio",
            "manual upload",
            "basic analytics",
            "limited AI questions",
            "delayed price refresh",
        ],
    ),
    BillingPlanOption(
        id="pro",
        name="Pro",
        price_label="Coming soon",
        features=[
            "multiple portfolios",
            "advanced analytics",
            "more AI questions",
            "export reports later",
            "faster price refresh",
        ],
        is_available=False,
    ),
    BillingPlanOption(
        id="premium_later",
        name="Premium Later",
        price_label="Later",
        features=[
            "broker sync",
            "weekly AI reports",
            "mobile alerts",
            "advanced diagnostics",
        ],
        is_available=False,
    ),
]


class BillingService:
    def __init__(self, db: Session):
        self.db = db
        self.usage_service = FeatureUsageSnapshotService(db)

    def get_plan(self, *, user: User) -> BillingPlanResponse:
        current_plan = self._current_plan(user=user)
        plans = [plan.model_copy(update={"is_current": plan.id == current_plan}) for plan in PLAN_OPTIONS]
        return BillingPlanResponse(
            current_plan=current_plan,
            status="placeholder",
            plans=plans,
            usage=self.usage_service.snapshot_for_user(user=user),
            message="Billing is a placeholder. No Stripe checkout is active yet.",
        )

    def create_checkout_session(self, *, user: User) -> CheckoutSessionResponse:
        return CheckoutSessionResponse(
            status="coming_soon",
            checkout_url=None,
            message="Checkout is coming soon. No payment session was created.",
        )

    def handle_webhook(self) -> BillingWebhookResponse:
        return BillingWebhookResponse(
            received=True,
            status="placeholder",
            message="Billing webhook placeholder received the request. No Stripe processing was performed.",
        )

    def _current_plan(self, *, user: User) -> str:
        subscription = self.db.scalar(
            select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.created_at.desc())
        )
        return subscription.plan_tier if subscription is not None else "free"
