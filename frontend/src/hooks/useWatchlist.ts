import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createWatchlistItem, deleteWatchlistItem, listWatchlist } from "../services/watchlistApi";
import type { WatchlistCreateInput } from "../types/watchlist";

export const watchlistQueryKey = ["watchlist"] as const;

export function useWatchlist() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: watchlistQueryKey,
    queryFn: listWatchlist
  });

  const createItem = useMutation({
    mutationFn: (input: WatchlistCreateInput) => createWatchlistItem(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: watchlistQueryKey });
    }
  });

  const deleteItem = useMutation({
    mutationFn: (watchlistItemId: string) => deleteWatchlistItem(watchlistItemId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: watchlistQueryKey });
    }
  });

  return {
    ...query,
    createItem,
    deleteItem
  };
}
