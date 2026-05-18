import { apiRequest } from "./apiClient";

export type UploadValidationResult = {
  upload_id: string;
  status: "pending" | "valid" | "invalid";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
};

export const uploadApi = {
  validateHoldings: (portfolioId: string, rows: unknown[]) =>
    apiRequest<UploadValidationResult>("/api/uploads/holdings/validate", {
      method: "POST",
      body: { portfolio_id: portfolioId, rows }
    })
};
