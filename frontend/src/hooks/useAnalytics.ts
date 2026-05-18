import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  getAllocation,
  getPerformance,
  getRisk,
  getRules,
  getSummary,
  recalculateAnalytics
} from "../services/analyticsApi";

export const analyticsQueryKey = (portfolioId: string | null | undefined) => ["analytics", portfolioId] as const;

export function useAnalytics(portfolioId: string | null | undefined) {
  const queryClient = useQueryClient();
  const enabled = Boolean(portfolioId);
  const queryKey = analyticsQueryKey(portfolioId);

  const summary = useQuery({
    queryKey: [...queryKey, "summary"],
    queryFn: () => getSummary(portfolioId!),
    enabled
  });

  const allocation = useQuery({
    queryKey: [...queryKey, "allocation"],
    queryFn: () => getAllocation(portfolioId!),
    enabled
  });

  const risk = useQuery({
    queryKey: [...queryKey, "risk"],
    queryFn: () => getRisk(portfolioId!),
    enabled
  });

  const performance = useQuery({
    queryKey: [...queryKey, "performance"],
    queryFn: () => getPerformance(portfolioId!),
    enabled
  });

  const rules = useQuery({
    queryKey: [...queryKey, "rules"],
    queryFn: () => getRules(portfolioId!),
    enabled
  });

  const recalculate = useMutation({
    mutationFn: () => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before recalculating analytics.");
      }
      return recalculateAnalytics(portfolioId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    }
  });

  return {
    summary,
    allocation,
    risk,
    performance,
    rules,
    recalculate,
    isLoading: summary.isLoading || allocation.isLoading || risk.isLoading || performance.isLoading || rules.isLoading,
    isError: summary.isError || allocation.isError || risk.isError || performance.isError || rules.isError,
    error:
      summary.error ??
      allocation.error ??
      risk.error ??
      performance.error ??
      rules.error ??
      null
  };
}
