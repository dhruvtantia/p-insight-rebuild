import type { DataStatus } from "./dataStatus";

export type MarketState = "open" | "closed" | "pre_open" | "post_close" | "unknown";

export type MarketStatus = {
  market: string;
  exchange: string | null;
  state: MarketState;
  timezone: string;
  as_of: string;
  next_open_at: string | null;
  next_close_at: string | null;
  data_status: DataStatus;
};

export type MarketIndexCard = {
  symbol: string;
  name: string;
  value: number;
  change: number | null;
  change_percent: number | null;
  currency: string;
  exchange: string | null;
  as_of: string;
  data_status: DataStatus;
};

export type SectorIndexCard = {
  symbol: string;
  name: string;
  sector: string;
  value: number;
  change: number | null;
  change_percent: number | null;
  exchange: string | null;
  as_of: string;
  data_status: DataStatus;
};

export type MarketMover = {
  symbol: string;
  company_name: string;
  last_price: number;
  change: number | null;
  change_percent: number;
  currency: string;
  exchange: string | null;
  sector: string | null;
  as_of: string;
  data_status: DataStatus;
};

export type MarketOverviewResponse = {
  market_status: MarketStatus;
  major_indices: MarketIndexCard[];
  sector_indices: SectorIndexCard[];
  top_gainers: MarketMover[];
  top_losers: MarketMover[];
  generated_at: string;
  data_status: DataStatus;
};
