import type { DataStatus } from "./dataStatus";

export type FundamentalMetrics = {
  pe_ratio: number | null;
  forward_pe: number | null;
  price_to_book: number | null;
  ev_to_ebitda: number | null;
  peg: number | null;
  roe: number | null;
  roa: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  revenue_growth: number | null;
  eps_growth: number | null;
  dividend_yield: number | null;
  debt_to_equity: number | null;
  market_cap: number | null;
};

export type FundamentalsCoverage = {
  provider: string;
  available_metrics: string[];
  missing_metrics: string[];
  coverage_ratio: number;
  is_complete: boolean;
};

export type AssetFundamentals = {
  symbol: string;
  company_name: string | null;
  currency: string;
  metrics: FundamentalMetrics;
  coverage: FundamentalsCoverage;
  as_of: string;
  source: string;
  data_status: DataStatus;
};

export type PortfolioFundamentalsCoverage = {
  covered_symbols: string[];
  missing_symbols: string[];
  coverage_percent: number;
  weighted_coverage_percent: number;
};

export type PortfolioWeightedMetrics = FundamentalMetrics;

export type MissingFundamentalsSymbol = string;

export type PortfolioFundamentals = {
  portfolio_id: string;
  fundamentals: AssetFundamentals[];
  weighted_metrics: PortfolioWeightedMetrics;
  coverage: PortfolioFundamentalsCoverage;
  missing_symbols: MissingFundamentalsSymbol[];
  data_status: DataStatus;
  warnings: string[];
};
