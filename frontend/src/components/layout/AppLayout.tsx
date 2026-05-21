import { Outlet, useLocation } from "react-router-dom";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { useAppStatus } from "../../hooks/useAppStatus";
import { DemoDataBanner } from "../ui";

const demoDataWarningPaths = new Set(["/market", "/dashboard", "/holdings", "/analytics", "/advisor", "/watchlist"]);
const mockMarketDataProviders = new Set(["mock", "mock_india"]);

export function AppLayout() {
  const location = useLocation();
  const appStatus = useAppStatus();
  const marketDataProvider = appStatus.data?.market_data_provider.trim().toLowerCase();
  const shouldShowDemoDataWarning =
    demoDataWarningPaths.has(location.pathname) && Boolean(marketDataProvider && mockMarketDataProviders.has(marketDataProvider));

  return (
    <div className="min-h-screen bg-surface text-ink">
      <div className="flex">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <Header />
          <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
            {shouldShowDemoDataWarning ? (
              <div className="mb-6">
                <DemoDataBanner />
              </div>
            ) : null}
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
