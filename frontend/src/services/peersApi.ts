import { apiRequest } from "./apiClient";
import type { PeerComparisonResponse } from "../types/peers";

export function getPeerComparison(portfolioId: string, symbol: string) {
  return apiRequest<PeerComparisonResponse>(
    `/api/portfolios/${portfolioId}/peers/${encodeURIComponent(symbol)}`
  );
}

export const peersApi = {
  getPeerComparison
};
