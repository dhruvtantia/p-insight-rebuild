export type SimulationRequest = {
  target_weights: Record<string, number>;
  added_symbols?: string[];
  removed_symbols?: string[];
};

export type AllocationLine = {
  symbol: string;
  current_value: number;
  weight: number;
  sector: string | null;
  asset_class: string | null;
};

export type SimulatedAllocationLine = {
  symbol: string;
  estimated_value: number;
  weight: number;
  current_value: number | null;
  is_added: boolean;
  is_removed: boolean;
  sector: string | null;
  asset_class: string | null;
};

export type SimulationConcentrationChange = {
  current_largest_symbol: string | null;
  simulated_largest_symbol: string | null;
  current_largest_weight: number;
  simulated_largest_weight: number;
  largest_weight_change: number;
  current_hhi: number;
  simulated_hhi: number;
  hhi_change: number;
};

export type EstimatedValueDistribution = {
  total_value: number;
  symbols: SimulatedAllocationLine[];
};

export type SimulationResponse = {
  portfolio_id: string;
  current_allocation: AllocationLine[];
  simulated_allocation: SimulatedAllocationLine[];
  concentration_change: SimulationConcentrationChange;
  estimated_value_distribution: EstimatedValueDistribution;
  warnings: string[];
  persisted: boolean;
};
