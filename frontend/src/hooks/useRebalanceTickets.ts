import { useMutation } from "@tanstack/react-query";

import { estimateRebalanceTickets } from "../services/rebalanceApi";
import type { RebalanceTicketRequest } from "../types/rebalance";

export function useRebalanceTickets(portfolioId: string | null | undefined) {
  const tickets = useMutation({
    mutationFn: (input: RebalanceTicketRequest) => {
      if (!portfolioId) {
        throw new Error("Select a portfolio before generating rebalance tickets.");
      }
      return estimateRebalanceTickets(portfolioId, input);
    }
  });

  return {
    tickets,
    estimateTickets: tickets.mutate,
    estimateTicketsAsync: tickets.mutateAsync
  };
}
