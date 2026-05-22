import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  confirmUpload,
  createUploadJob,
  getMappingSuggestions,
  getUploadErrors,
  getUploadJob,
  submitColumnMapping,
  validateUpload
} from "../services/uploadApi";
import type { ColumnMapping } from "../types/upload";

export function useUpload(uploadJobId: string | null, portfolioId: string | null) {
  const queryClient = useQueryClient();

  const uploadJob = useQuery({
    queryKey: ["uploadJob", uploadJobId],
    queryFn: () => getUploadJob(uploadJobId!),
    enabled: Boolean(uploadJobId)
  });

  const uploadErrors = useQuery({
    queryKey: ["uploadErrors", uploadJobId],
    queryFn: () => getUploadErrors(uploadJobId!),
    enabled: Boolean(uploadJobId)
  });

  const mappingSuggestions = useQuery({
    queryKey: ["uploadMappingSuggestions", uploadJobId],
    queryFn: () => getMappingSuggestions(uploadJobId!),
    enabled: Boolean(uploadJobId),
    retry: false
  });

  const createUpload = useMutation({
    mutationFn: ({ targetPortfolioId, file }: { targetPortfolioId: string; file: File }) =>
      createUploadJob(targetPortfolioId, file),
    onSuccess: (data) => {
      void queryClient.setQueryData(["uploadJob", data.id], data);
      void queryClient.invalidateQueries({ queryKey: ["uploadMappingSuggestions", data.id] });
    }
  });

  const submitMapping = useMutation({
    mutationFn: ({ targetUploadJobId, mapping }: { targetUploadJobId: string; mapping: ColumnMapping }) =>
      submitColumnMapping(targetUploadJobId, mapping),
    onSuccess: (data) => {
      void queryClient.setQueryData(["uploadJob", data.upload_job.id], data.upload_job);
    }
  });

  const validate = useMutation({
    mutationFn: (targetUploadJobId: string) => validateUpload(targetUploadJobId),
    onSuccess: (data) => {
      void queryClient.setQueryData(["uploadJob", data.upload_job.id], data.upload_job);
      void queryClient.invalidateQueries({ queryKey: ["uploadErrors", data.upload_job.id] });
    }
  });

  const confirm = useMutation({
    mutationFn: (targetUploadJobId: string) => confirmUpload(targetUploadJobId),
    onSuccess: (_data) => {
      void queryClient.invalidateQueries({ queryKey: ["portfolios"] });
      void queryClient.invalidateQueries({ queryKey: ["holdings"] });
      if (portfolioId) {
        void queryClient.invalidateQueries({ queryKey: ["holdings", portfolioId] });
      }
    }
  });

  return {
    uploadJob,
    uploadErrors,
    mappingSuggestions,
    createUpload,
    submitMapping,
    validate,
    confirm
  };
}

export function useUploadMappingSuggestions(uploadJobId: string | null) {
  return useQuery({
    queryKey: ["uploadMappingSuggestions", uploadJobId],
    queryFn: () => getMappingSuggestions(uploadJobId!),
    enabled: Boolean(uploadJobId),
    retry: false
  });
}
