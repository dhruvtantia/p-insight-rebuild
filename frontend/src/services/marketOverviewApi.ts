import { apiRequest } from "./apiClient";
import type { MarketOverviewResponse } from "../types/marketOverview";

export function getMarketOverview() {
  return apiRequest<MarketOverviewResponse>("/api/market/overview");
}

export const marketOverviewApi = {
  getMarketOverview
};
