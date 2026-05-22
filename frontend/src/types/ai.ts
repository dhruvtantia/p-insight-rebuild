import type { DataStatus } from "./dataStatus";

export type AIProviderMetadata = {
  provider: string;
  model: string;
  mode?: string | null;
  is_mock?: boolean;
};

export type AIAdvisorStructuredResponse = {
  summary?: string;
  insights?: string[];
  warnings?: string[];
  suggestions?: string[];
  limitations?: string[];
  follow_up_questions?: string[];
  provider_metadata?: AIProviderMetadata;
};

export type AIAdvisorPortfolioSummary = {
  id?: string;
  name?: string;
  base_currency?: string;
  benchmark_symbol?: string | null;
  risk_free_rate?: number | null;
  total_portfolio_value?: number;
  total_cost_basis?: number;
  total_unrealized_gain_loss?: number;
  total_unrealized_gain_loss_pct?: number | null;
  largest_holding?: { symbol?: string; weight?: number } | null;
  holdings_count?: number;
};

export type AIAdvisorHoldingContext = {
  symbol?: string;
  company_name?: string | null;
  quantity?: number;
  average_cost?: number | null;
  current_price?: number | null;
  currency?: string;
  sector?: string | null;
  asset_class?: string | null;
};

export type AIAdvisorRuleInsight = {
  rule_id?: string;
  severity?: "low" | "medium" | "high";
  title?: string;
  message?: string;
  affected_symbols?: string[];
};

export type AIAdvisorPriceFreshness = {
  priced_symbols?: string[];
  missing_price_symbols?: string[];
  latest_price_as_of?: string | null;
  latest_price_source?: string | null;
};

export type AIAdvisorOptionalContext = {
  dashboard_summary?: Record<string, unknown>;
  performance_history_summary?: {
    method?: string;
    benchmark_symbol?: string | null;
    missing_price_symbols?: string[];
    data_status?: DataStatus;
    assumptions?: Record<string, unknown>;
  } & Record<string, unknown>;
  risk_v2_summary?: Record<string, unknown>;
  fundamentals_summary?: {
    coverage?: Record<string, unknown>;
    missing_symbols?: string[];
    warnings?: string[];
    data_status?: DataStatus;
  } & Record<string, unknown>;
  peer_summary?: {
    symbol?: string;
    peer_symbols?: string[];
    peer_set_quality?: Record<string, unknown>;
    warnings?: string[];
  } & Record<string, unknown>;
  snapshot_change_summary?: {
    snapshot_count?: number;
    latest_snapshot?: Record<string, unknown> | null;
    latest_change?: Record<string, unknown> | null;
  } & Record<string, unknown>;
};

export type AIAdvisorContext = {
  portfolio_summary?: AIAdvisorPortfolioSummary;
  holdings?: AIAdvisorHoldingContext[];
  risk_metrics?: Record<string, unknown>;
  allocation?: Record<string, unknown>;
  rule_based_insights?: AIAdvisorRuleInsight[];
  price_freshness?: AIAdvisorPriceFreshness;
  optional_context?: AIAdvisorOptionalContext;
  user_question?: string;
};

export type AIAdvisorResponse = {
  conversation_id: string;
  mode: "summary" | "question";
  provider: string;
  model: string;
  response: string;
  context: AIAdvisorContext;
  structured_response?: AIAdvisorStructuredResponse | null;
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
  structured_response?: AIAdvisorStructuredResponse | null;
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
