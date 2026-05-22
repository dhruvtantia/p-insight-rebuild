import { apiRequest } from "./apiClient";
import type { AssetFundamentals, PortfolioFundamentals } from "../types/fundamentals";

export function getAssetFundamentals(symbol: string) {
  return apiRequest<AssetFundamentals>(`/api/assets/${encodeURIComponent(symbol)}/fundamentals`);
}

export function getPortfolioFundamentals(portfolioId: string) {
  return apiRequest<PortfolioFundamentals>(`/api/portfolios/${portfolioId}/fundamentals`);
}

export const fundamentalsApi = {
  getAssetFundamentals,
  getPortfolioFundamentals
};
