export type RebalanceTicketRequest = {
  target_weights: Record<string, number>;
  cash_contribution?: number | null;
  cash_withdrawal?: number | null;
};

export type RebalanceTicketAction = "buy" | "sell" | "hold";

export type RebalanceTicket = {
  symbol: string;
  current_weight: number;
  target_weight: number;
  current_value: number;
  target_value: number;
  action: RebalanceTicketAction;
  estimated_shares_to_trade: number;
  estimated_cash_needed: number;
  estimated_cash_generated: number;
};

export type RebalanceTicketsResponse = {
  portfolio_id: string;
  tickets: RebalanceTicket[];
  current_portfolio_value: number;
  target_portfolio_value: number;
  estimated_cash_needed: number;
  estimated_cash_generated: number;
  leftover_cash: number;
  warnings: string[];
  execution_required: boolean;
};
