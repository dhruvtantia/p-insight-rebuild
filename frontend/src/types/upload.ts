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
  status: string;
};

export type ColumnMapping = Record<string, string>;

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
  skipped_count: number;
  invalid_rows: number;
  warnings: string[];
  created_holding_ids: string[];
};

export type UploadErrorsResponse = {
  upload_job_id: string;
  errors: UploadRow[];
};
