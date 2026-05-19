const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

type JsonRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function apiRequest<T>(path: string, options: JsonRequestOptions = {}): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const requestBody =
    options.body === undefined ? undefined : isFormData ? (options.body as FormData) : JSON.stringify(options.body);
  const headers = isFormData
    ? options.headers
    : {
        "Content-Type": "application/json",
        ...options.headers
      };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: requestBody
  }).catch((error) => {
    throw new ApiError(
      "Backend API unavailable. Make sure the FastAPI server is running and VITE_API_BASE_URL is correct.",
      0,
      error
    );
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const apiMessage = payload?.error?.message ?? payload?.detail ?? "API request failed";
    throw new ApiError(apiMessage, response.status, payload?.error?.details ?? payload);
  }

  return payload as T;
}
