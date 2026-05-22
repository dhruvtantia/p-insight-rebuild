import { useQuery } from "@tanstack/react-query";

import { getPerformanceHistory } from "../services/performanceApi";
import type { HistoricalPeriod } from "../types/performance";

export function usePerformanceHistory(
  portfolioId: string | null | undefined,
  period: HistoricalPeriod,
  options: { enabled?: boolean } = {}
) {
  return useQuery({
    queryKey: ["performanceHistory", portfolioId, period],
    queryFn: () => getPerformanceHistory(portfolioId!, period),
    enabled: Boolean(portfolioId) && (options.enabled ?? true),
    retry: false
  });
}
