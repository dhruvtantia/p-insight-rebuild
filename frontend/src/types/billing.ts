export type PlanTier = "free" | "pro" | "premium_later";

export type BillingPlan = {
  id: PlanTier;
  name: string;
  price_label: string;
  features: string[];
  is_current: boolean;
  is_available: boolean;
};

export type BillingPlanResponse = {
  current_plan: PlanTier;
  status: string;
  plans: BillingPlan[];
  usage: {
    portfolio_count: number;
    holdings_count: number;
    ai_conversation_count: number;
    enforcement_enabled: boolean;
  };
  message: string;
};

export type CheckoutSessionResponse = {
  status: string;
  checkout_url: string | null;
  message: string;
};
