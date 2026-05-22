import { type MouseEvent as ReactMouseEvent, useCallback, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { useAppStatus } from "../../hooks/useAppStatus";
import { DemoDataBanner } from "../ui";

const sidebarWidthStorageKey = "pinsight.sidebarWidth";
const defaultSidebarWidth = 256;
const minSidebarWidth = 220;
const maxSidebarWidth = 360;
const demoDataWarningPaths = new Set(["/market", "/dashboard", "/holdings", "/analytics", "/advisor", "/watchlist"]);
const mockMarketDataProviders = new Set(["mock", "mock_india"]);

function clampSidebarWidth(width: number) {
  return Math.min(maxSidebarWidth, Math.max(minSidebarWidth, width));
}

function getSidebarStorage() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    return window.localStorage ?? null;
  } catch {
    return null;
  }
}

function getInitialSidebarWidth() {
  const storage = getSidebarStorage();
  if (!storage) {
    return defaultSidebarWidth;
  }

  const storedWidth = Number(storage.getItem(sidebarWidthStorageKey));
  return Number.isFinite(storedWidth) ? clampSidebarWidth(storedWidth) : defaultSidebarWidth;
}

export function AppLayout() {
  const location = useLocation();
  const appStatus = useAppStatus();
  const [sidebarWidth, setSidebarWidth] = useState(getInitialSidebarWidth);
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const marketDataProvider = appStatus.data?.market_data_provider.trim().toLowerCase();
  const shouldShowDemoDataWarning =
    demoDataWarningPaths.has(location.pathname) && Boolean(marketDataProvider && mockMarketDataProviders.has(marketDataProvider));

  useEffect(() => {
    try {
      getSidebarStorage()?.setItem(sidebarWidthStorageKey, String(sidebarWidth));
    } catch {
      // Keep resizing available even when browser storage is disabled.
    }
  }, [sidebarWidth]);

  useEffect(() => {
    if (!isResizingSidebar) {
      return;
    }

    const handleMouseMove = (event: MouseEvent) => {
      setSidebarWidth(clampSidebarWidth(event.clientX));
    };
    const stopResizing = () => {
      setIsResizingSidebar(false);
    };

    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", stopResizing);

    return () => {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizingSidebar]);

  const startSidebarResize = useCallback((event: ReactMouseEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsResizingSidebar(true);
  }, []);

  return (
    <div className="min-h-screen bg-surface text-ink">
      <div className="flex">
        <Sidebar width={sidebarWidth} />
        <div
          className="group hidden w-2 shrink-0 cursor-col-resize items-stretch justify-center lg:flex"
          role="separator"
          aria-label="Resize sidebar"
          aria-orientation="vertical"
          aria-valuemin={minSidebarWidth}
          aria-valuemax={maxSidebarWidth}
          aria-valuenow={sidebarWidth}
          onMouseDown={startSidebarResize}
        >
          <div className="h-full w-px bg-line transition group-hover:bg-accent" />
        </div>
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
