import { useMutation } from "@tanstack/react-query";

import { optimizePortfolio } from "../services/optimizerApi";
import type { OptimizerRequest } from "../types/optimizer";

export function useOptimizer(portfolioId: string | null | undefined) {
  const optimization = useMutation({
    mutationFn: (input: OptimizerRequest) => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before running the optimizer.");
      }
      return optimizePortfolio(portfolioId, input);
    }
  });

  return {
    optimization,
    optimize: optimization.mutate,
    optimizeAsync: optimization.mutateAsync
  };
}
