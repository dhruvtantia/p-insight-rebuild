import { apiRequest } from "./apiClient";
import type { HistoricalPeriod, PortfolioPerformanceHistory } from "../types/performance";

export function getPerformanceHistory(portfolioId: string, period: HistoricalPeriod) {
  return apiRequest<PortfolioPerformanceHistory>(
    `/api/portfolios/${portfolioId}/performance/history?period=${encodeURIComponent(period)}`
  );
}

export const performanceApi = {
  getPerformanceHistory
};
