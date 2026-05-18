import { apiRequest } from "./apiClient";
import type { BillingPlan } from "../types/billing";

export const billingApi = {
  getPlans: () => apiRequest<BillingPlan[]>("/api/billing/plans"),
  getUsage: () => apiRequest<Record<string, unknown>>("/api/billing/usage")
};
