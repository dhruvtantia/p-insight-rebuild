import { apiRequest } from "./apiClient";
import type { OptimizerRequest, OptimizerResponse } from "../types/optimizer";

export function optimizePortfolio(portfolioId: string, input: OptimizerRequest) {
  return apiRequest<OptimizerResponse>(`/api/portfolios/${portfolioId}/optimize`, {
    method: "POST",
    body: input
  });
}

export const optimizerApi = {
  optimizePortfolio
};
