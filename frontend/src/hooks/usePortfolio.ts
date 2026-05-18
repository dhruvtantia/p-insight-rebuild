import { useQuery } from "@tanstack/react-query";

import { getPortfolio } from "../services/portfolioApi";

export function usePortfolio(portfolioId: string | null | undefined) {
  return useQuery({
    queryKey: ["portfolio", portfolioId],
    queryFn: () => getPortfolio(portfolioId!),
    enabled: Boolean(portfolioId)
  });
}
