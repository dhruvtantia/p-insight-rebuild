import { useQuery } from "@tanstack/react-query";

import { getAssetFundamentals, getPortfolioFundamentals } from "../services/fundamentalsApi";

export const portfolioFundamentalsQueryKey = (portfolioId: string | null | undefined) =>
  ["portfolioFundamentals", portfolioId] as const;

export function usePortfolioFundamentals(portfolioId: string | null | undefined) {
  return useQuery({
    queryKey: portfolioFundamentalsQueryKey(portfolioId),
    queryFn: () => getPortfolioFundamentals(portfolioId!),
    enabled: Boolean(portfolioId),
    retry: false
  });
}

export function useAssetFundamentals(symbol: string | null | undefined, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: ["assetFundamentals", symbol],
    queryFn: () => getAssetFundamentals(symbol!),
    enabled: Boolean(symbol) && (options.enabled ?? true),
    retry: false
  });
}

export function useFundamentals(portfolioId: string | null | undefined) {
  return usePortfolioFundamentals(portfolioId);
}
