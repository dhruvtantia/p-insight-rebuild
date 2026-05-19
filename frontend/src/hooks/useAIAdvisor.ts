import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  askPortfolioQuestion,
  generatePortfolioSummary,
  getConversation,
  listConversations
} from "../services/aiApi";

export const aiAdvisorQueryKey = (portfolioId: string | null | undefined) => ["ai-advisor", portfolioId] as const;

export function useAIAdvisor(portfolioId: string | null | undefined) {
  const queryClient = useQueryClient();
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const enabled = Boolean(portfolioId);
  const queryKey = aiAdvisorQueryKey(portfolioId);

  const conversations = useQuery({
    queryKey: [...queryKey, "conversations"],
    queryFn: () => listConversations(portfolioId!),
    enabled
  });

  const selectedConversation = useQuery({
    queryKey: ["ai-conversation", selectedConversationId],
    queryFn: () => getConversation(selectedConversationId!),
    enabled: Boolean(selectedConversationId)
  });

  const generateSummary = useMutation({
    mutationFn: () => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before generating a summary.");
      }
      return generatePortfolioSummary(portfolioId);
    },
    onSuccess: (response) => {
      setSelectedConversationId(response.conversation_id);
      void queryClient.invalidateQueries({ queryKey: [...queryKey, "conversations"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-conversation", response.conversation_id] });
    }
  });

  const askQuestion = useMutation({
    mutationFn: (question: string) => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before asking a question.");
      }
      return askPortfolioQuestion(portfolioId, question);
    },
    onSuccess: (response) => {
      setSelectedConversationId(response.conversation_id);
      void queryClient.invalidateQueries({ queryKey: [...queryKey, "conversations"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-conversation", response.conversation_id] });
    }
  });

  return {
    conversations,
    selectedConversation,
    selectedConversationId,
    setSelectedConversationId,
    generateSummary,
    askQuestion,
    isLoading: conversations.isLoading,
    isError: conversations.isError,
    error: conversations.error
  };
}
