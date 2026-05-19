export type AIAdvisorContext = {
  portfolio_summary: Record<string, unknown>;
  holdings: Array<Record<string, unknown>>;
  risk_metrics: Record<string, unknown>;
  allocation: Record<string, unknown>;
  rule_based_insights: Array<Record<string, unknown>>;
  price_freshness: Record<string, unknown>;
  user_question: string;
};

export type AIAdvisorResponse = {
  conversation_id: string;
  mode: "summary" | "question";
  provider: string;
  model: string;
  response: string;
  context: AIAdvisorContext;
  created_at: string;
};

export type AIMessageResponse = {
  id: string;
  conversation_id: string;
  role: "system" | "user" | "assistant";
  content: string;
  provider: string | null;
  model: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

export type AIConversationListItem = {
  id: string;
  portfolio_id: string;
  title: string | null;
  mode: string | null;
  created_at: string;
  updated_at: string;
};

export type AIConversationDetail = {
  id: string;
  portfolio_id: string;
  title: string | null;
  mode: string | null;
  context: AIAdvisorContext;
  messages: AIMessageResponse[];
  created_at: string;
  updated_at: string;
};
