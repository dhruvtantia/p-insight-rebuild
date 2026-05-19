export type WatchlistItem = {
  id: string;
  user_id: string;
  symbol: string;
  name: string | null;
  notes: string | null;
  current_price: number | null;
  price_currency: string | null;
  price_source: string | null;
  price_as_of: string | null;
  created_at: string;
  updated_at: string;
};

export type WatchlistCreateInput = {
  symbol: string;
  name?: string | null;
  notes?: string | null;
};
