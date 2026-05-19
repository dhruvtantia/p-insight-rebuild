import { apiRequest } from "./apiClient";
import type { AIAdvisorResponse, AIConversationDetail, AIConversationListItem } from "../types/ai";

export function generatePortfolioSummary(portfolioId: string) {
  return apiRequest<AIAdvisorResponse>(`/api/portfolios/${portfolioId}/ai/summary`, {
    method: "POST",
    body: {}
  });
}

export function askPortfolioQuestion(portfolioId: string, question: string) {
  return apiRequest<AIAdvisorResponse>(`/api/portfolios/${portfolioId}/ai/question`, {
    method: "POST",
    body: { question }
  });
}

export function listConversations(portfolioId: string) {
  return apiRequest<AIConversationListItem[]>(`/api/portfolios/${portfolioId}/ai/conversations`);
}

export function getConversation(conversationId: string) {
  return apiRequest<AIConversationDetail>(`/api/ai/conversations/${conversationId}`);
}

export const aiApi = {
  generatePortfolioSummary,
  askPortfolioQuestion,
  listConversations,
  getConversation
};
