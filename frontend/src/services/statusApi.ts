import { apiRequest } from "./apiClient";
import type { AppStatus } from "../types/appStatus";

export function getAppStatus() {
  return apiRequest<AppStatus>("/api/status");
}

export const statusApi = {
  getAppStatus
};
