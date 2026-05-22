import { useQuery } from "@tanstack/react-query";

import { getRiskV2 } from "../services/riskApi";
import type { HistoricalPeriod } from "../types/performance";

export function useRiskV2(
  portfolioId: string | null | undefined,
  period: HistoricalPeriod,
  options: { enabled?: boolean } = {}
) {
  return useQuery({
    queryKey: ["riskV2", portfolioId, period],
    queryFn: () => getRiskV2(portfolioId!, period),
    enabled: Boolean(portfolioId) && (options.enabled ?? true),
    retry: false
  });
}
