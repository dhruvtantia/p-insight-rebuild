export type AIAdvisorMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

export type AIAdvisorResponse = {
  answer: string;
  is_mock: boolean;
  context_summary: string;
};
