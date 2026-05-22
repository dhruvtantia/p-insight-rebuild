import { apiRequest } from "./apiClient";
import type { HistoricalPeriod } from "../types/performance";
import type { RiskV2Response } from "../types/risk";

export function getRiskV2(portfolioId: string, period: HistoricalPeriod) {
  return apiRequest<RiskV2Response>(`/api/portfolios/${portfolioId}/risk?period=${encodeURIComponent(period)}`);
}

export const riskApi = {
  getRiskV2
};
