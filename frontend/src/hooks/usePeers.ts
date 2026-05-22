import { useQuery } from "@tanstack/react-query";

import { getPeerComparison } from "../services/peersApi";

export const peerComparisonQueryKey = (portfolioId: string | null | undefined, symbol: string | null | undefined) =>
  ["peerComparison", portfolioId, symbol] as const;

export function usePeerComparison(portfolioId: string | null | undefined, symbol: string | null | undefined) {
  return useQuery({
    queryKey: peerComparisonQueryKey(portfolioId, symbol),
    queryFn: () => getPeerComparison(portfolioId!, symbol!),
    enabled: Boolean(portfolioId && symbol),
    retry: false
  });
}
