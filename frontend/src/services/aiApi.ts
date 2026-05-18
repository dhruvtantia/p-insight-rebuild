import { apiRequest } from "./apiClient";
import type { AIAdvisorResponse } from "../types/ai";

export const aiApi = {
  askAdvisor: (portfolioId: string, question: string) =>
    apiRequest<AIAdvisorResponse>(`/api/portfolios/${portfolioId}/advisor/questions`, {
      method: "POST",
      body: { question }
    })
};
