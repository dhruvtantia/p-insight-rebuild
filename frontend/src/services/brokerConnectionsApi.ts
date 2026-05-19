import { apiRequest } from "./apiClient";
import type { BrokerConnection, BrokerProviderPlaceholder } from "../types/brokerConnections";

export function listBrokerConnections() {
  return apiRequest<BrokerConnection[]>("/api/broker-connections");
}

export function listBrokerProviders() {
  return apiRequest<BrokerProviderPlaceholder[]>("/api/broker-connections/providers");
}

export function createBrokerPlaceholder(provider: string) {
  return apiRequest<BrokerConnection>("/api/broker-connections/connect-placeholder", {
    method: "POST",
    body: { provider }
  });
}

export function deleteBrokerConnection(connectionId: string) {
  return apiRequest<void>(`/api/broker-connections/${connectionId}`, {
    method: "DELETE"
  });
}

export const brokerConnectionsApi = {
  listBrokerConnections,
  listBrokerProviders,
  createBrokerPlaceholder,
  deleteBrokerConnection
};
