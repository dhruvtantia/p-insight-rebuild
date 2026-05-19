import { apiRequest } from "./apiClient";
import type { DemoSeedResponse } from "../types/demo";

export function seedDemoPortfolio() {
  return apiRequest<DemoSeedResponse>("/api/demo/seed", {
    method: "POST"
  });
}

export const demoApi = {
  seedDemoPortfolio
};
