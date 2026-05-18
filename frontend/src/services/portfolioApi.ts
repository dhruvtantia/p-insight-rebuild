import { apiRequest } from "./apiClient";
import type { Portfolio, PortfolioCreateInput, PortfolioUpdateInput } from "../types/portfolio";

export function listPortfolios() {
  return apiRequest<Portfolio[]>("/api/portfolios");
}

export function getPortfolio(portfolioId: string) {
  return apiRequest<Portfolio>(`/api/portfolios/${portfolioId}`);
}

export function createPortfolio(input: PortfolioCreateInput) {
  return apiRequest<Portfolio>("/api/portfolios", {
    method: "POST",
    body: input
  });
}

export function updatePortfolio(portfolioId: string, input: PortfolioUpdateInput) {
  return apiRequest<Portfolio>(`/api/portfolios/${portfolioId}`, {
    method: "PATCH",
    body: input
  });
}

export function deletePortfolio(portfolioId: string) {
  return apiRequest<void>(`/api/portfolios/${portfolioId}`, {
    method: "DELETE"
  });
}

export const portfolioApi = {
  list: listPortfolios,
  get: getPortfolio,
  create: createPortfolio,
  update: updatePortfolio,
  remove: deletePortfolio,
  listPortfolios,
  getPortfolio,
  createPortfolio,
  updatePortfolio,
  deletePortfolio
};
