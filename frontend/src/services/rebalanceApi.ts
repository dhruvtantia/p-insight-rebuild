import { apiRequest } from "./apiClient";
import type { RebalanceTicketRequest, RebalanceTicketsResponse } from "../types/rebalance";

export function estimateRebalanceTickets(portfolioId: string, input: RebalanceTicketRequest) {
  return apiRequest<RebalanceTicketsResponse>(`/api/portfolios/${portfolioId}/rebalance/tickets`, {
    method: "POST",
    body: input
  });
}

export const rebalanceApi = {
  estimateRebalanceTickets
};
