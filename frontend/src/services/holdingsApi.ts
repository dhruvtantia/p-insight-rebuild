import { apiRequest } from "./apiClient";
import type { Holding, HoldingCreateInput, HoldingUpdateInput } from "../types/holdings";

export function listHoldings(portfolioId: string) {
  return apiRequest<Holding[]>(`/api/portfolios/${portfolioId}/holdings`);
}

export function createHolding(portfolioId: string, input: HoldingCreateInput) {
  return apiRequest<Holding>(`/api/portfolios/${portfolioId}/holdings`, {
    method: "POST",
    body: input
  });
}

export function updateHolding(portfolioId: string, holdingId: string, input: HoldingUpdateInput) {
  return apiRequest<Holding>(`/api/portfolios/${portfolioId}/holdings/${holdingId}`, {
    method: "PATCH",
    body: input
  });
}

export function deleteHolding(portfolioId: string, holdingId: string) {
  return apiRequest<void>(`/api/portfolios/${portfolioId}/holdings/${holdingId}`, {
    method: "DELETE"
  });
}

export const holdingsApi = {
  list: listHoldings,
  create: createHolding,
  update: updateHolding,
  remove: deleteHolding,
  listHoldings,
  createHolding,
  updateHolding,
  deleteHolding
};
