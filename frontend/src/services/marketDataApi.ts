import { apiRequest } from "./apiClient";

export type PriceQuote = {
  symbol: string;
  price: number;
  currency: string;
  source: string;
  as_of: string;
  is_realtime: boolean;
};

export type BatchPriceResponse = {
  prices: PriceQuote[];
};

export type PriceHistoryPoint = {
  symbol: string;
  date: string;
  close: number;
  currency: string;
  source: string;
};

export type PriceHistoryResponse = {
  symbol: string;
  start: string;
  end: string;
  prices: PriceHistoryPoint[];
};

export type HoldingPriceRefreshItem = {
  holding_id: string;
  symbol: string;
  previous_price: number | null;
  current_price: number;
  currency: string;
  source: string;
  as_of: string;
  is_realtime: boolean;
};

export type PortfolioPriceRefreshResponse = {
  portfolio_id: string;
  refreshed_count: number;
  prices: PriceQuote[];
  holdings: HoldingPriceRefreshItem[];
};

export function getBatchPrices(symbols: string[]) {
  const params = new URLSearchParams({ symbols: symbols.join(",") });
  return apiRequest<BatchPriceResponse>(`/api/market-data/prices?${params.toString()}`);
}

export function getPrice(symbol: string) {
  return apiRequest<PriceQuote>(`/api/market-data/prices/${encodeURIComponent(symbol)}`);
}

export function getPriceHistory(symbol: string, options: { start?: string; end?: string } = {}) {
  const params = new URLSearchParams();
  if (options.start) {
    params.set("start", options.start);
  }
  if (options.end) {
    params.set("end", options.end);
  }

  const query = params.toString();
  return apiRequest<PriceHistoryResponse>(
    `/api/market-data/history/${encodeURIComponent(symbol)}${query ? `?${query}` : ""}`
  );
}

export function refreshPortfolioPrices(portfolioId: string) {
  return apiRequest<PortfolioPriceRefreshResponse>(`/api/portfolios/${portfolioId}/prices/refresh`, {
    method: "POST"
  });
}

export const marketDataApi = {
  getBatchPrices,
  getPrice,
  getPriceHistory,
  refreshPortfolioPrices
};
