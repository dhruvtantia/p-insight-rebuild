import { apiRequest } from "./apiClient";
import type { AnalyticsSummary } from "../types/analytics";

export const analyticsApi = {
  getPortfolioAnalytics: (portfolioId: string) =>
    apiRequest<AnalyticsSummary>(`/api/portfolios/${portfolioId}/analytics`)
};
