import { apiRequest } from "./apiClient";
import type {
  ColumnMapping,
  ColumnMappingResponse,
  ConfirmUploadResponse,
  UploadErrorsResponse,
  UploadJob,
  ValidateUploadResponse
} from "../types/upload";

export function createUploadJob(portfolioId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return apiRequest<UploadJob>(`/api/portfolios/${portfolioId}/uploads`, {
    method: "POST",
    body: formData
  });
}

export function getUploadJob(uploadJobId: string) {
  return apiRequest<UploadJob>(`/api/uploads/${uploadJobId}`);
}

export function submitColumnMapping(uploadJobId: string, mapping: ColumnMapping) {
  return apiRequest<ColumnMappingResponse>(`/api/uploads/${uploadJobId}/column-mapping`, {
    method: "POST",
    body: { mapping }
  });
}

export function validateUpload(uploadJobId: string) {
  return apiRequest<ValidateUploadResponse>(`/api/uploads/${uploadJobId}/validate`, {
    method: "POST"
  });
}

export function confirmUpload(uploadJobId: string) {
  return apiRequest<ConfirmUploadResponse>(`/api/uploads/${uploadJobId}/confirm`, {
    method: "POST"
  });
}

export function getUploadErrors(uploadJobId: string) {
  return apiRequest<UploadErrorsResponse>(`/api/uploads/${uploadJobId}/errors`);
}

export const uploadApi = {
  createUploadJob,
  getUploadJob,
  submitColumnMapping,
  validateUpload,
  confirmUpload,
  getUploadErrors
};
