import type { DataStatus } from "./dataStatus";
import type { HistoricalPeriod } from "./performance";

export type OptimizerRequest = {
  period: HistoricalPeriod;
  frontier_points?: number;
};

export type OptimizerAssumptions = {
  long_only: boolean;
  no_taxes: boolean;
  no_transaction_costs: boolean;
  no_liquidity_constraints: boolean;
  historical_estimates_only: boolean;
  not_investment_advice: boolean;
};

export type OptimizerMetricSet = {
  expected_annual_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
};

export type OptimizedWeights = {
  target_weights: Record<string, number>;
  metrics: OptimizerMetricSet;
};

export type EfficientFrontierPoint = {
  index: number;
  target_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  weights: Record<string, number>;
};

export type OptimizerStatus = "ok" | "insufficient_history" | "unsupported";

export type OptimizerResponse = {
  portfolio_id: string;
  period: HistoricalPeriod;
  generated_at: string;
  status: OptimizerStatus;
  current_portfolio_metrics: OptimizerMetricSet;
  current_weights: Record<string, number>;
  min_variance_target_weights: OptimizedWeights;
  max_sharpe_target_weights: OptimizedWeights;
  efficient_frontier_points: EfficientFrontierPoint[];
  assumptions: OptimizerAssumptions;
  data_status: DataStatus;
  warnings: string[];
};
