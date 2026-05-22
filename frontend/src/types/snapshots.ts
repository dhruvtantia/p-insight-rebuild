import type { AllocationBucket, ConcentrationRisk } from "./analytics";

export type SnapshotCreateInput = {
  label?: string | null;
};

export type SnapshotPrice = {
  symbol: string;
  current_price: number | null;
  currency: string;
};

export type SnapshotHolding = {
  holding_id: string;
  symbol: string;
  company_name: string | null;
  quantity: number;
  average_cost: number | null;
  current_price: number | null;
  currency: string;
  sector: string | null;
  asset_class: string | null;
  exchange: string | null;
  market_value: number | null;
  cost_basis: number | null;
  weight: number;
};

export type SnapshotSummary = {
  id: string;
  portfolio_id: string;
  label: string | null;
  as_of: string;
  total_value: number;
  holdings_value: number;
  cash_value: number | null;
  cost_basis: number;
  holdings_count: number;
  created_at: string;
};

export type Snapshot = SnapshotSummary & {
  holdings: SnapshotHolding[];
  prices: SnapshotPrice[];
  sector_allocation: AllocationBucket[];
  concentration_summary: ConcentrationRisk;
  generated_at: string;
};

export type SnapshotListResponse = SnapshotSummary[];

export type QuantityChange = {
  symbol: string;
  from_quantity: number;
  to_quantity: number;
  quantity_change: number;
};

export type HoldingValueChange = {
  symbol: string;
  from_value: number | null;
  to_value: number | null;
  value_change: number | null;
};

export type SnapshotValueChanges = {
  from_total_value: number;
  to_total_value: number;
  total_value_change: number;
  holdings: HoldingValueChange[];
};

export type SectorAllocationChange = {
  name: string;
  from_value: number;
  to_value: number;
  value_change: number;
  from_weight: number;
  to_weight: number;
  weight_change: number;
};

export type ConcentrationChange = {
  from_status: string;
  to_status: string;
  from_largest_symbol: string | null;
  to_largest_symbol: string | null;
  from_top_5_weight: number;
  to_top_5_weight: number;
  top_5_weight_change: number;
};

export type SnapshotComparisonResponse = {
  portfolio_id: string;
  from_snapshot_id: string;
  to_snapshot_id: string;
  added_holdings: SnapshotHolding[];
  removed_holdings: SnapshotHolding[];
  quantity_changes: QuantityChange[];
  value_changes: SnapshotValueChanges;
  sector_allocation_changes: SectorAllocationChange[];
  concentration_changes: ConcentrationChange | null;
};
