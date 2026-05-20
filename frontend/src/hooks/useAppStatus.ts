import { useQuery } from "@tanstack/react-query";

import { getAppStatus } from "../services/statusApi";

export const appStatusQueryKey = ["app-status"] as const;

export function useAppStatus() {
  return useQuery({
    queryKey: appStatusQueryKey,
    queryFn: getAppStatus,
    staleTime: 5 * 60 * 1000
  });
}
