import { Outlet } from "react-router-dom";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-surface text-ink">
      <div className="flex">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <Header />
          <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
