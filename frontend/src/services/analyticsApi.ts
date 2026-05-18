import { apiRequest } from "./apiClient";
import type {
  AllocationAnalytics,
  AnalyticsRecalculateResponse,
  PerformanceAnalytics,
  PortfolioAnalyticsSummary,
  RiskAnalytics,
  RuleInsight
} from "../types/analytics";

const analyticsPath = (portfolioId: string, path: string) => `/api/portfolios/${portfolioId}/analytics/${path}`;

export function getSummary(portfolioId: string) {
  return apiRequest<PortfolioAnalyticsSummary>(analyticsPath(portfolioId, "summary"));
}

export function getAllocation(portfolioId: string) {
  return apiRequest<AllocationAnalytics>(analyticsPath(portfolioId, "allocation"));
}

export function getRisk(portfolioId: string) {
  return apiRequest<RiskAnalytics>(analyticsPath(portfolioId, "risk"));
}

export function getPerformance(portfolioId: string) {
  return apiRequest<PerformanceAnalytics>(analyticsPath(portfolioId, "performance"));
}

export function getRules(portfolioId: string) {
  return apiRequest<RuleInsight[]>(analyticsPath(portfolioId, "rules"));
}

export function recalculateAnalytics(portfolioId: string) {
  return apiRequest<AnalyticsRecalculateResponse>(analyticsPath(portfolioId, "recalculate"), {
    method: "POST"
  });
}

export const analyticsApi = {
  getSummary,
  getAllocation,
  getRisk,
  getPerformance,
  getRules,
  recalculateAnalytics
};
