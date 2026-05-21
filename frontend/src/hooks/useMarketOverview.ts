import { useQuery } from "@tanstack/react-query";

import { getMarketOverview } from "../services/marketOverviewApi";

export const marketOverviewQueryKey = ["market-overview"] as const;

export function useMarketOverview() {
  return useQuery({
    queryKey: marketOverviewQueryKey,
    queryFn: getMarketOverview,
    staleTime: 60 * 1000
  });
}
