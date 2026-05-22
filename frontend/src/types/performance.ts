import type { DataStatus } from "./dataStatus";

export type HistoricalPeriod = "1M" | "3M" | "6M" | "1Y" | "5Y";

export type PerformanceAssumptions = {
  method: "synthetic_current_holdings";
  assumes_current_quantities_held_throughout: boolean;
  not_transaction_aware: boolean;
  not_xirr: boolean;
  not_time_weighted_return: boolean;
};

export type PortfolioValuePoint = {
  date: string;
  value: number;
  currency: string;
};

export type NormalizedReturnPoint = {
  date: string;
  normalized_return: number;
};

export type PortfolioPerformanceHistory = {
  portfolio_id: string;
  period: HistoricalPeriod;
  start_date: string;
  end_date: string;
  generated_at: string;
  base_currency: string;
  benchmark_symbol: string;
  portfolio_value_series: PortfolioValuePoint[];
  portfolio_normalized_return_series: NormalizedReturnPoint[];
  benchmark_normalized_return_series: NormalizedReturnPoint[];
  missing_price_symbols: string[];
  assumptions: PerformanceAssumptions;
  data_status: DataStatus;
};
