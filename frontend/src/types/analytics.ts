export type AllocationSlice = {
  label: string;
  market_value: number;
  weight: number;
};

export type AnalyticsSummary = {
  portfolio_id: string;
  total_market_value: number;
  allocation: AllocationSlice[];
  insights: Array<{
    severity: "info" | "warning" | "success";
    title: string;
    detail: string;
  }>;
};
