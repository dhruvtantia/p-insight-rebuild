import { apiRequest } from "./apiClient";
import type { Snapshot, SnapshotComparisonResponse, SnapshotCreateInput, SnapshotListResponse } from "../types/snapshots";

const snapshotsPath = (portfolioId: string) => `/api/portfolios/${portfolioId}/snapshots`;

export function listSnapshots(portfolioId: string) {
  return apiRequest<SnapshotListResponse>(snapshotsPath(portfolioId));
}

export function createSnapshot(portfolioId: string, input: SnapshotCreateInput = {}) {
  return apiRequest<Snapshot>(snapshotsPath(portfolioId), {
    method: "POST",
    body: input
  });
}

export function compareSnapshots(portfolioId: string, fromId: string, toId: string) {
  const params = new URLSearchParams({ from_id: fromId, to_id: toId });
  return apiRequest<SnapshotComparisonResponse>(`${snapshotsPath(portfolioId)}/compare?${params.toString()}`);
}

export const snapshotsApi = {
  listSnapshots,
  createSnapshot,
  compareSnapshots
};
