export type BrokerProviderPlaceholder = {
  provider: string;
  display_name: string;
  status: "coming_soon";
  message: string;
};

export type BrokerConnection = {
  id: string;
  provider: string;
  status: string;
  message: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};
