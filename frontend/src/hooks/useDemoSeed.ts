import { useMutation, useQueryClient } from "@tanstack/react-query";

import { seedDemoPortfolio } from "../services/demoApi";
import { analyticsQueryKey } from "./useAnalytics";
import { portfoliosQueryKey } from "./usePortfolios";

export function useDemoSeed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: seedDemoPortfolio,
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: portfoliosQueryKey });
      void queryClient.invalidateQueries({ queryKey: ["holdings", result.portfolio_id] });
      void queryClient.invalidateQueries({ queryKey: analyticsQueryKey(result.portfolio_id) });
    }
  });
}
