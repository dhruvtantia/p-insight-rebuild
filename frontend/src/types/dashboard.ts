import type { DataStatus } from "./dataStatus";

export type DashboardKpis = {
  portfolio_id: string;
  base_currency: string;
  total_invested: number;
  current_value: number;
  unrealized_pnl: number;
  return_percent: number | null;
  holdings_count: number;
  priced_holdings_count: number;
  largest_holding_symbol: string | null;
  largest_holding_weight: number | null;
  cash_weight: number | null;
};

export type DashboardTopHolding = {
  holding_id: string;
  symbol: string;
  company_name: string | null;
  market_value: number;
  weight: number;
  unrealized_gain_loss: number | null;
  unrealized_gain_loss_pct: number | null;
  currency: string;
};

export type DashboardAllocationItem = {
  dimension: "asset_class" | "sector" | "currency";
  name: string;
  value: number;
  weight: number;
  symbols: string[];
};

export type DashboardRiskSummary = {
  concentration_status: "empty" | "ok" | "moderate" | "high";
  largest_holding_symbol: string | null;
  largest_holding_weight: number | null;
  top_3_weight: number;
  hhi: number;
  volatility: number | null;
  volatility_status: "ok" | "insufficient_history";
  sharpe_ratio: number | null;
  sharpe_ratio_status: "ok" | "insufficient_history";
  max_drawdown: number | null;
  max_drawdown_status: "ok" | "insufficient_history";
  message: string;
};

export type DashboardDataQuality = {
  holdings_count: number;
  priced_holdings_count: number;
  missing_price_count: number;
  missing_cost_basis_count: number;
  stale_price_count: number;
  warnings: string[];
  data_status: DataStatus;
};

export type DashboardActionItem = {
  id: string;
  priority: "low" | "medium" | "high";
  category: "setup" | "data_quality" | "risk" | "allocation" | "performance";
  title: string;
  message: string;
  affected_symbols: string[];
  recommended_action:
    | "add_holdings"
    | "refresh_prices"
    | "review_holdings"
    | "review_allocation"
    | "review_risk"
    | "review_performance"
    | null;
};

export type DashboardBundleResponse = {
  portfolio_id: string;
  generated_at: string;
  kpis: DashboardKpis;
  sector_allocation: DashboardAllocationItem[];
  asset_allocation: DashboardAllocationItem[];
  top_holdings: DashboardTopHolding[];
  risk: DashboardRiskSummary;
  data_quality: DashboardDataQuality;
  action_items: DashboardActionItem[];
  data_status: DataStatus;
};
