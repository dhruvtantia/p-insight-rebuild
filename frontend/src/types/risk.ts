import type { DataStatus } from "./dataStatus";
import type { HistoricalPeriod, PerformanceAssumptions } from "./performance";

export type RiskMetricStatusCode =
  | "ok"
  | "insufficient_history"
  | "partial_data"
  | "missing_benchmark"
  | "undefined";

export type RiskMetricStatus = {
  status: RiskMetricStatusCode;
  message: string;
};

export type RiskV2Response = {
  portfolio_id: string;
  period: HistoricalPeriod;
  generated_at: string;
  benchmark_symbol: string;
  observations: number;
  annualized_return: number | null;
  annualized_volatility: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number | null;
  downside_deviation: number | null;
  value_at_risk_95: number | null;
  beta_vs_benchmark: number | null;
  tracking_error: number | null;
  information_ratio: number | null;
  correlation_matrix: Record<string, Record<string, number | null>> | null;
  metric_status: Record<string, RiskMetricStatus>;
  assumptions: PerformanceAssumptions;
  data_status: DataStatus;
};
