import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { AdminPage } from "../pages/AdminPage";
import { AIAdvisorPage } from "../pages/AIAdvisorPage";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { BillingPage } from "../pages/BillingPage";
import { BrokerConnectionsPage } from "../pages/BrokerConnectionsPage";
import { ChangesPage } from "../pages/ChangesPage";
import { DashboardPage } from "../pages/DashboardPage";
import { FundamentalsPage } from "../pages/FundamentalsPage";
import { HoldingsPage } from "../pages/HoldingsPage";
import { LandingPage } from "../pages/LandingPage";
import { LoginPage, SignupPage } from "../pages/AuthPages";
import { MarketPage } from "../pages/MarketPage";
import { OnboardingPage } from "../pages/OnboardingPage";
import { PeersPage } from "../pages/PeersPage";
import { SettingsPage } from "../pages/SettingsPage";
import { UploadPage } from "../pages/UploadPage";
import { WatchlistPage } from "../pages/WatchlistPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: "login", element: <LoginPage /> },
      { path: "signup", element: <SignupPage /> },
      { path: "onboarding", element: <OnboardingPage /> },
      { path: "market", element: <MarketPage /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "changes", element: <ChangesPage /> },
      { path: "holdings", element: <HoldingsPage /> },
      { path: "upload", element: <UploadPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
      { path: "fundamentals", element: <FundamentalsPage /> },
      { path: "peers", element: <PeersPage /> },
      { path: "advisor", element: <AIAdvisorPage /> },
      { path: "watchlist", element: <WatchlistPage /> },
      { path: "brokers", element: <BrokerConnectionsPage /> },
      { path: "billing", element: <BillingPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "admin", element: <AdminPage /> }
    ]
  }
]);
