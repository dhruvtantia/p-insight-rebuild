import { apiRequest } from "./apiClient";
import type { SimulationRequest, SimulationResponse } from "../types/simulator";

export function simulatePortfolio(portfolioId: string, input: SimulationRequest) {
  return apiRequest<SimulationResponse>(`/api/portfolios/${portfolioId}/simulate`, {
    method: "POST",
    body: input
  });
}

export const simulatorApi = {
  simulatePortfolio
};
