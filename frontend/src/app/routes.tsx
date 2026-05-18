import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "../components/layout/AppLayout";
import { AdminPage } from "../pages/AdminPage";
import { AIAdvisorPage } from "../pages/AIAdvisorPage";
import { AnalyticsPage } from "../pages/AnalyticsPage";
import { BillingPage } from "../pages/BillingPage";
import { BrokerConnectionsPage } from "../pages/BrokerConnectionsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { HoldingsPage } from "../pages/HoldingsPage";
import { LandingPage } from "../pages/LandingPage";
import { LoginPage, SignupPage } from "../pages/AuthPages";
import { OnboardingPage } from "../pages/OnboardingPage";
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
      { path: "dashboard", element: <DashboardPage /> },
      { path: "holdings", element: <HoldingsPage /> },
      { path: "upload", element: <UploadPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
      { path: "advisor", element: <AIAdvisorPage /> },
      { path: "watchlist", element: <WatchlistPage /> },
      { path: "brokers", element: <BrokerConnectionsPage /> },
      { path: "billing", element: <BillingPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "admin", element: <AdminPage /> }
    ]
  }
]);
