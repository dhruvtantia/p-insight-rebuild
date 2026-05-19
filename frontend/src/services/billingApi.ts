import { apiRequest } from "./apiClient";
import type { BillingPlanResponse, CheckoutSessionResponse } from "../types/billing";

export const billingApi = {
  getPlan: () => apiRequest<BillingPlanResponse>("/api/billing/plan"),
  createCheckoutSession: () =>
    apiRequest<CheckoutSessionResponse>("/api/billing/create-checkout-session", {
      method: "POST"
    })
};
