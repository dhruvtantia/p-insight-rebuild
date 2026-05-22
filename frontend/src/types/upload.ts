export type UploadJob = {
  id: string;
  portfolio_id: string;
  filename: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  detected_columns: string[];
  preview_rows: Array<Record<string, unknown>>;
  created_at: string;
  updated_at: string;
};

export type UploadRow = {
  id: string;
  row_number: number;
  raw_data: Record<string, unknown>;
  mapped_data: Record<string, unknown>;
  validation_errors: string[];
  warnings: string[];
  status: string;
};

export type ColumnMapping = Record<string, string>;

export type UploadTargetField =
  | "symbol"
  | "quantity"
  | "average_cost"
  | "market_value"
  | "company_name"
  | "sector"
  | "asset_class"
  | "exchange"
  | "currency";

export type ColumnMappingSuggestion = {
  target_field: UploadTargetField;
  source_column: string;
  confidence: number;
  reason: string;
};

export type ColumnMappingSuggestionsResponse = {
  upload_job_id: string;
  detected_columns: string[];
  suggestions: ColumnMappingSuggestion[];
};

export type ColumnMappingResponse = {
  upload_job: UploadJob;
  mapping: ColumnMapping;
  mapped_preview_rows: Array<Record<string, unknown>>;
};

export type ValidateUploadResponse = {
  upload_job: UploadJob;
  rows: UploadRow[];
};

export type ConfirmUploadResponse = {
  upload_job_id: string;
  status: "imported" | "partial_imported";
  imported_count: number;
  invalid_count: number;
  duplicate_count: number;
  skipped_count: number;
  invalid_rows: number;
  warnings: string[];
  rejected_row_reasons: RejectedUploadRowReason[];
  created_holding_ids: string[];
};

export type RejectedUploadRowReason = {
  row_number: number;
  symbol: string | null;
  reasons: string[];
};

export type UploadErrorsResponse = {
  upload_job_id: string;
  errors: UploadRow[];
};
