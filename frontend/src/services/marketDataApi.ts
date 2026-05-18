import { apiRequest } from "./apiClient";

export type Quote = {
  symbol: string;
  price: number;
  currency: string;
  as_of: string;
};

export const marketDataApi = {
  getQuotes: (symbols: string[]) => apiRequest<Quote[]>(`/api/market-data/quotes?symbols=${symbols.join(",")}`),
  getProviders: () => apiRequest<Array<{ id: string; name: string }>>("/api/market-data/providers")
};
