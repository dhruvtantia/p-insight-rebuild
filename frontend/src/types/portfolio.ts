export type Portfolio = {
  id: string;
  user_id: string;
  name: string;
  base_currency: string;
  benchmark_symbol: string | null;
  risk_free_rate: number | null;
  created_at: string;
  updated_at: string;
};

export type PortfolioCreateInput = {
  name: string;
  base_currency?: string;
  benchmark_symbol?: string | null;
  risk_free_rate?: number | null;
};

export type PortfolioUpdateInput = Partial<PortfolioCreateInput>;
