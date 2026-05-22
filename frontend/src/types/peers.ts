import type { AssetFundamentals } from "./fundamentals";

export type PeerCompany = AssetFundamentals;

export type MetricDirection = "lower_is_better" | "higher_is_better";

export type PeerSetQuality = {
  source: "static_india_peer_map";
  is_static: boolean;
  peer_count: number;
  covered_peer_count: number;
  missing_peer_symbols: string[];
  coverage_percent: number;
  is_sparse: boolean;
};

export type MetricComparisonRow = {
  metric: string;
  direction: MetricDirection;
  selected_value: number | null;
  peer_values: Record<string, number | null>;
  peer_average: number | null;
  selected_rank: number | null;
};

export type PeerQualityWarning = string;

export type PeerComparisonResponse = {
  portfolio_id: string;
  symbol: string;
  selected_company: PeerCompany;
  peer_companies: PeerCompany[];
  metric_comparison_table: MetricComparisonRow[];
  simple_ranks: Record<string, Record<string, number | null>>;
  peer_set_quality: PeerSetQuality;
  warnings: PeerQualityWarning[];
};
