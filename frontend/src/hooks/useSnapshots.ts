import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { compareSnapshots, createSnapshot, listSnapshots } from "../services/snapshotsApi";
import type { SnapshotCreateInput } from "../types/snapshots";

export const snapshotsQueryKey = (portfolioId: string | null | undefined) => ["snapshots", portfolioId] as const;

export function useSnapshots(portfolioId: string | null | undefined) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: snapshotsQueryKey(portfolioId),
    queryFn: () => listSnapshots(portfolioId!),
    enabled: Boolean(portfolioId),
    retry: false
  });

  const createMutation = useMutation({
    mutationFn: (input: SnapshotCreateInput) => createSnapshot(portfolioId!, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: snapshotsQueryKey(portfolioId) });
      void queryClient.invalidateQueries({ queryKey: ["snapshotComparison", portfolioId] });
    }
  });

  return {
    ...query,
    createSnapshot: createMutation
  };
}

export function useSnapshotComparison(
  portfolioId: string | null | undefined,
  fromSnapshotId: string | null | undefined,
  toSnapshotId: string | null | undefined
) {
  return useQuery({
    queryKey: ["snapshotComparison", portfolioId, fromSnapshotId, toSnapshotId],
    queryFn: () => compareSnapshots(portfolioId!, fromSnapshotId!, toSnapshotId!),
    enabled: Boolean(portfolioId && fromSnapshotId && toSnapshotId && fromSnapshotId !== toSnapshotId),
    retry: false
  });
}
