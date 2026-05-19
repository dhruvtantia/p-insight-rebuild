from pydantic import BaseModel


class BillingPlanFeature(BaseModel):
    label: str


class BillingPlanOption(BaseModel):
    id: str
    name: str
    price_label: str
    features: list[str]
    is_current: bool = False
    is_available: bool = True


class BillingPlanResponse(BaseModel):
    current_plan: str
    status: str
    plans: list[BillingPlanOption]
    usage: dict
    message: str


class CheckoutSessionResponse(BaseModel):
    status: str
    checkout_url: str | None
    message: str


class BillingWebhookResponse(BaseModel):
    received: bool
    status: str
    message: str
