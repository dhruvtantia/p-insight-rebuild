import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createPortfolio,
  deletePortfolio,
  listPortfolios,
  updatePortfolio
} from "../services/portfolioApi";
import type { PortfolioCreateInput, PortfolioUpdateInput } from "../types/portfolio";

export const portfoliosQueryKey = ["portfolios"] as const;

export function usePortfolios() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: portfoliosQueryKey,
    queryFn: listPortfolios
  });

  const createMutation = useMutation({
    mutationFn: (input: PortfolioCreateInput) => createPortfolio(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: portfoliosQueryKey });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ portfolioId, input }: { portfolioId: string; input: PortfolioUpdateInput }) =>
      updatePortfolio(portfolioId, input),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: portfoliosQueryKey });
      void queryClient.invalidateQueries({ queryKey: ["portfolio", variables.portfolioId] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (portfolioId: string) => deletePortfolio(portfolioId),
    onSuccess: (_data, portfolioId) => {
      void queryClient.invalidateQueries({ queryKey: portfoliosQueryKey });
      void queryClient.removeQueries({ queryKey: ["portfolio", portfolioId] });
      void queryClient.removeQueries({ queryKey: ["holdings", portfolioId] });
    }
  });

  return {
    ...query,
    createPortfolio: createMutation,
    updatePortfolio: updateMutation,
    deletePortfolio: deleteMutation
  };
}
