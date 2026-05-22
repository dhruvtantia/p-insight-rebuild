import { useQuery } from "@tanstack/react-query";

import { getDashboardBundle } from "../services/dashboardApi";

export const dashboardBundleQueryKey = (portfolioId: string | null | undefined) => ["dashboard-bundle", portfolioId] as const;

export function useDashboardBundle(portfolioId: string | null | undefined) {
  return useQuery({
    queryKey: dashboardBundleQueryKey(portfolioId),
    queryFn: () => getDashboardBundle(portfolioId!),
    enabled: Boolean(portfolioId),
    retry: false
  });
}
