import { apiRequest } from "./apiClient";
import type { DashboardBundleResponse } from "../types/dashboard";

export function getDashboardBundle(portfolioId: string) {
  return apiRequest<DashboardBundleResponse>(`/api/portfolios/${portfolioId}/dashboard`);
}

export const dashboardApi = {
  getDashboardBundle
};
