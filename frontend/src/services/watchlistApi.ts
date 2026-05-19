import { apiRequest } from "./apiClient";
import type { WatchlistCreateInput, WatchlistItem } from "../types/watchlist";

export function listWatchlist() {
  return apiRequest<WatchlistItem[]>("/api/watchlist");
}

export function createWatchlistItem(input: WatchlistCreateInput) {
  return apiRequest<WatchlistItem>("/api/watchlist", {
    method: "POST",
    body: input
  });
}

export function deleteWatchlistItem(watchlistItemId: string) {
  return apiRequest<void>(`/api/watchlist/${watchlistItemId}`, {
    method: "DELETE"
  });
}

export const watchlistApi = {
  listWatchlist,
  createWatchlistItem,
  deleteWatchlistItem
};
