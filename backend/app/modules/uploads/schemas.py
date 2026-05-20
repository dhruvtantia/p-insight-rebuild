from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.uploads.column_detection import ColumnMappingSuggestion

SUPPORTED_UPLOAD_FIELDS = {
    "symbol",
    "company_name",
    "quantity",
    "average_cost",
    "market_value",
    "currency",
    "sector",
    "asset_class",
    "exchange",
}

REQUIRED_UPLOAD_FIELDS = {"symbol", "quantity"}


class UploadRowResponse(BaseModel):
    id: str
    row_number: int
    raw_data: dict
    mapped_data: dict
    validation_errors: list[str]
    warnings: list[str] = Field(default_factory=list)
    status: str


class UploadJobResponse(BaseModel):
    id: str
    portfolio_id: str
    filename: str
    status: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    detected_columns: list[str]
    preview_rows: list[dict]
    created_at: datetime
    updated_at: datetime


class ColumnMappingRequest(BaseModel):
    mapping: dict[str, str] = Field(
        description="Mapping from P-insight field name to uploaded source column name"
    )


class ColumnMappingResponse(BaseModel):
    upload_job: UploadJobResponse
    mapping: dict[str, str]
    mapped_preview_rows: list[dict]


class ColumnMappingSuggestionsResponse(BaseModel):
    upload_job_id: str
    detected_columns: list[str]
    suggestions: list[ColumnMappingSuggestion]


class ValidateUploadResponse(BaseModel):
    upload_job: UploadJobResponse
    rows: list[UploadRowResponse]


class RejectedUploadRowReason(BaseModel):
    row_number: int
    symbol: str | None = None
    reasons: list[str]


class ConfirmUploadResponse(BaseModel):
    upload_job_id: str
    status: Literal["imported", "partial_imported"]
    imported_count: int
    invalid_count: int
    duplicate_count: int
    skipped_count: int
    invalid_rows: int
    warnings: list[str]
    rejected_row_reasons: list[RejectedUploadRowReason] = Field(default_factory=list)
    created_holding_ids: list[str]


class UploadErrorsResponse(BaseModel):
    upload_job_id: str
    errors: list[UploadRowResponse]
