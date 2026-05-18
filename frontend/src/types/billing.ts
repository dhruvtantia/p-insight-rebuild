export type PlanTier = "free" | "pro" | "premium_later";

export type BillingPlan = {
  id: PlanTier;
  name: string;
  price_label: string;
  features: string[];
};
