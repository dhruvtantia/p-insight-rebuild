export type HoldingAnalytics = {
  holding_id: string;
  symbol: string;
  quantity: number;
  average_cost: number | null;
  current_price: number | null;
  currency: string;
  sector: string | null;
  asset_class: string | null;
  market_value: number | null;
  cost_basis: number | null;
  unrealized_gain_loss: number | null;
  unrealized_gain_loss_pct: number | null;
  weight: number;
};

export type AllocationBucket = {
  name: string;
  value: number;
  weight: number;
  symbols: string[];
};

export type LargestHolding = {
  symbol: string;
  market_value: number;
  weight: number;
};

export type PerformanceHolding = {
  symbol: string;
  unrealized_gain_loss: number;
  unrealized_gain_loss_pct: number | null;
};

export type PerformanceAnalytics = {
  total_cost_basis: number;
  total_unrealized_gain_loss: number;
  total_unrealized_gain_loss_pct: number | null;
  top_gainers: PerformanceHolding[];
  top_losers: PerformanceHolding[];
};

export type AllocationAnalytics = {
  asset_allocation: AllocationBucket[];
  sector_allocation: AllocationBucket[];
  currency_exposure: AllocationBucket[];
};

export type ConcentrationRisk = {
  status: "empty" | "ok" | "moderate" | "high";
  largest_holding: LargestHolding | null;
  top_5_weight: number;
  message: string;
};

export type RiskMetric = {
  value: number | null;
  status: "ok" | "insufficient_history";
  message: string;
};

export type RiskAnalytics = {
  volatility: RiskMetric;
  sharpe_ratio: RiskMetric;
  max_drawdown: RiskMetric;
  concentration: ConcentrationRisk;
};

export type RuleInsight = {
  rule_id: string;
  severity: "low" | "medium" | "high";
  title: string;
  message: string;
  affected_symbols: string[];
};

export type PortfolioAnalyticsSummary = {
  portfolio_id: string;
  base_currency: string;
  total_portfolio_value: number;
  total_cost_basis: number;
  total_unrealized_gain_loss: number;
  total_unrealized_gain_loss_pct: number | null;
  holdings: HoldingAnalytics[];
  largest_holding: LargestHolding | null;
};

export type PortfolioAnalyticsBundle = {
  portfolio_id: string;
  generated_at: string;
  summary: PortfolioAnalyticsSummary;
  allocation: AllocationAnalytics;
  risk: RiskAnalytics;
  performance: PerformanceAnalytics;
  rules: RuleInsight[];
};

export type AnalyticsSnapshotRecord = {
  id: string;
  result_type: string;
};

export type AnalyticsRecalculateResponse = {
  portfolio_id: string;
  generated_at: string;
  stored_results: AnalyticsSnapshotRecord[];
  analytics: PortfolioAnalyticsBundle;
};
