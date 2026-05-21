export type DataStatus = {
  source: string;
  provider: string;
  is_mock: boolean;
  is_realtime: boolean;
  as_of: string | null;
  is_stale: boolean;
  warning: string | null;
};
