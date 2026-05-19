import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createBrokerPlaceholder,
  deleteBrokerConnection,
  listBrokerConnections,
  listBrokerProviders
} from "../services/brokerConnectionsApi";

const brokerConnectionsQueryKey = ["broker-connections"] as const;
const brokerProvidersQueryKey = ["broker-connections", "providers"] as const;

export function useBrokerConnections() {
  const queryClient = useQueryClient();

  const connections = useQuery({
    queryKey: brokerConnectionsQueryKey,
    queryFn: listBrokerConnections
  });

  const providers = useQuery({
    queryKey: brokerProvidersQueryKey,
    queryFn: listBrokerProviders
  });

  const createPlaceholder = useMutation({
    mutationFn: (provider: string) => createBrokerPlaceholder(provider),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: brokerConnectionsQueryKey });
    }
  });

  const deleteConnection = useMutation({
    mutationFn: (connectionId: string) => deleteBrokerConnection(connectionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: brokerConnectionsQueryKey });
    }
  });

  return {
    connections,
    providers,
    createPlaceholder,
    deleteConnection,
    isLoading: connections.isLoading || providers.isLoading,
    isError: connections.isError || providers.isError,
    error: connections.error ?? providers.error ?? null
  };
}
