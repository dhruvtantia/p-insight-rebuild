import { useMutation, useQueryClient } from "@tanstack/react-query";

import { refreshPortfolioPrices } from "../services/marketDataApi";

export function usePortfolioPrices(portfolioId: string | null | undefined) {
  const queryClient = useQueryClient();

  const refreshPrices = useMutation({
    mutationFn: () => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before refreshing prices.");
      }
      return refreshPortfolioPrices(portfolioId);
    },
    onSuccess: () => {
      if (!portfolioId) {
        return;
      }
      void queryClient.invalidateQueries({ queryKey: ["holdings", portfolioId] });
      void queryClient.invalidateQueries({ queryKey: ["portfolio", portfolioId] });
    }
  });

  return {
    refreshPrices
  };
}
