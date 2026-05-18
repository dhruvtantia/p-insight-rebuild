import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createHolding,
  deleteHolding,
  listHoldings,
  updateHolding
} from "../services/holdingsApi";
import type { HoldingCreateInput, HoldingUpdateInput } from "../types/holdings";

export function useHoldings(portfolioId: string | null | undefined) {
  const queryClient = useQueryClient();
  const queryKey = ["holdings", portfolioId] as const;

  const query = useQuery({
    queryKey,
    queryFn: () => listHoldings(portfolioId!),
    enabled: Boolean(portfolioId)
  });

  const createMutation = useMutation({
    mutationFn: (input: HoldingCreateInput) => createHolding(portfolioId!, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ holdingId, input }: { holdingId: string; input: HoldingUpdateInput }) =>
      updateHolding(portfolioId!, holdingId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (holdingId: string) => deleteHolding(portfolioId!, holdingId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey });
    }
  });

  return {
    ...query,
    createHolding: createMutation,
    updateHolding: updateMutation,
    deleteHolding: deleteMutation
  };
}
