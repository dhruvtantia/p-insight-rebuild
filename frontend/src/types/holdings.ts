export type Holding = {
  id: string;
  portfolio_id: string;
  symbol: string;
  company_name: string | null;
  quantity: number;
  average_cost: number | null;
  current_price: number | null;
  market_value: number | null;
  unrealized_gain_loss: number | null;
  currency: string;
  sector: string | null;
  asset_class: string | null;
  exchange: string | null;
  created_at: string;
  updated_at: string;
};

export type HoldingCreateInput = {
  symbol: string;
  company_name?: string | null;
  quantity: number;
  average_cost?: number | null;
  current_price?: number | null;
  currency?: string;
  sector?: string | null;
  asset_class?: string | null;
  exchange?: string | null;
};

export type HoldingUpdateInput = Partial<HoldingCreateInput>;
